"""
Ingest frozen study data into kintsugi.db (SQLite).

Sources:
  - dataset/CodeWorkout/Problem_Prompts/problem_prompts.csv  → kcs, problems, problem_kcs
  - scripts/annotation_tool/annotation_inputs/student_*.json → submissions.code + score
  - results/human_validation/ablation/llm_ablation_deepseek_baseline_*.json → submission_gaps
  - results/learning_curve/exp16_predictions_30students.csv  → recurrence (Gemini-estimated)

Cluster fallback: students not found in exp16 default to 'average'.
Reasoning: not captured in study data; field left empty for source='study'.
"""

import json
import os
import sqlite3
from pathlib import Path
from collections import defaultdict

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO = Path(__file__).resolve().parents[2]
DB_PATH = Path(__file__).resolve().parent.parent / "kintsugi.db"

PROBLEM_PROMPTS = REPO / "dataset" / "CodeWorkout" / "Problem_Prompts" / "problem_prompts.csv"
ANNOTATION_INPUTS = REPO / "scripts" / "annotation_tool" / "annotation_inputs"
ABLATION_DIR = REPO / "results" / "human_validation" / "ablation"
EXP16_PREDICTIONS = REPO / "results" / "learning_curve" / "exp16_predictions_30students.csv"

# The 10 students whose DeepSeek baseline annotations exist
DEEPSEEK_STUDENTS = [10155, 9948, 14189, 14352, 14362, 14363, 14374, 14414, 14474, 14499]

# Known clusters; 4 students absent from exp16 default to 'average'
# The ablation study selected struggling students (more non-perfect submissions to annotate).
# For the 4 not present in exp16 predictions, fall back to 'struggling'.
CLUSTER_FALLBACK = "struggling"  # all ablation students are struggling

# ---------------------------------------------------------------------------
# KC metadata
# ---------------------------------------------------------------------------

STRUCTURAL_KCS = {"If/Else", "NestedIf", "While", "For", "NestedFor"}

ALL_KCS = [
    "If/Else", "NestedIf", "While", "For", "NestedFor",
    "Math+-*/", "Math%", "LogicAndNotOr", "LogicCompareNum", "LogicBoolean",
    "StringFormat", "StringConcat", "StringIndex", "StringLen",
    "StringEqual", "CharEqual", "ArrayIndex", "DefFunction",
]

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS kcs (
    name TEXT PRIMARY KEY,
    kind TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,
    cluster TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS problems (
    id INTEGER PRIMARY KEY,
    assignment_id INTEGER NOT NULL,
    requirement TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS problem_kcs (
    problem_id INTEGER NOT NULL REFERENCES problems(id),
    kc TEXT NOT NULL REFERENCES kcs(name),
    PRIMARY KEY (problem_id, kc)
);

CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id),
    problem_id INTEGER NOT NULL REFERENCES problems(id),
    score REAL NOT NULL,
    reasoning TEXT NOT NULL DEFAULT '',
    code TEXT NOT NULL DEFAULT '',
    parse_status TEXT NOT NULL DEFAULT 'ok',
    attempt_order INTEGER NOT NULL,
    source TEXT NOT NULL DEFAULT 'study'
);

CREATE TABLE IF NOT EXISTS submission_gaps (
    submission_id INTEGER NOT NULL REFERENCES submissions(id),
    kc TEXT NOT NULL REFERENCES kcs(name),
    PRIMARY KEY (submission_id, kc)
);

CREATE TABLE IF NOT EXISTS recurrence (
    kc TEXT NOT NULL REFERENCES kcs(name),
    cluster TEXT NOT NULL,
    hit_rate REAL NOT NULL,
    n INTEGER NOT NULL,
    PRIMARY KEY (kc, cluster)
);
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_cluster_map():
    df = pd.read_csv(EXP16_PREDICTIONS)
    # Normalize cluster names to lowercase for consistent lookup
    df["Cluster"] = df["Cluster"].str.lower().str.replace(" ", "_")
    return df.drop_duplicates("SubjectID").set_index("SubjectID")["Cluster"].to_dict()


def load_problem_prompts():
    """Returns (problems_df, kc_columns list)."""
    df = pd.read_csv(PROBLEM_PROMPTS)
    kc_cols = ALL_KCS  # same order as CSV columns
    return df, kc_cols


def load_annotation_input(student_id: int) -> dict:
    path = ANNOTATION_INPUTS / f"student_{student_id}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_deepseek_baseline(student_id: int) -> dict:
    path = ABLATION_DIR / f"llm_ablation_deepseek_baseline_{student_id}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def compute_recurrence(cluster_map: dict) -> dict:
    """
    Returns {(kc, cluster): (hit_rate, n)} from exp16 Gemini predictions.
    Labeled in DB as Gemini-estimated (DeepSeek ≈ Gemini, κ 0.535 vs 0.548).
    """
    df = pd.read_csv(EXP16_PREDICTIONS)
    df["Cluster"] = df["Cluster"].str.lower().str.replace(" ", "_")
    result = {}
    for (kc, cluster), group in df.groupby(["GapKC", "Cluster"]):
        tp = (group["Prediction"] == "TP").sum()
        n = len(group)
        result[(kc, cluster)] = (tp / n if n > 0 else 0.0, n)
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Removed existing {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    print(f"Created schema in {DB_PATH}")

    cluster_map = load_cluster_map()
    problems_df, kc_cols = load_problem_prompts()

    # --- 1. kcs ---
    for kc in ALL_KCS:
        kind = "structural" if kc in STRUCTURAL_KCS else "specific"
        conn.execute("INSERT OR IGNORE INTO kcs (name, kind) VALUES (?, ?)", (kc, kind))
    conn.commit()
    print(f"Inserted {len(ALL_KCS)} KCs")

    # --- 2. problems + problem_kcs ---
    problem_assignment = {}  # problem_id → assignment_id (for sorting)
    for _, row in problems_df.iterrows():
        pid = int(row["ProblemID"])
        aid = int(row["AssignmentID"])
        req = str(row.get("Requirement", ""))
        problem_assignment[pid] = aid
        conn.execute(
            "INSERT OR IGNORE INTO problems (id, assignment_id, requirement) VALUES (?, ?, ?)",
            (pid, aid, req),
        )
        for kc in kc_cols:
            if row.get(kc, 0) == 1:
                conn.execute(
                    "INSERT OR IGNORE INTO problem_kcs (problem_id, kc) VALUES (?, ?)",
                    (pid, kc),
                )
    conn.commit()
    print(f"Inserted {len(problems_df)} problems with KC mappings")

    # --- 3. students + submissions + submission_gaps ---
    total_subs = 0
    total_gaps = 0

    for student_id in DEEPSEEK_STUDENTS:
        cluster = cluster_map.get(student_id, CLUSTER_FALLBACK)
        conn.execute(
            "INSERT OR IGNORE INTO students (id, cluster) VALUES (?, ?)",
            (student_id, cluster),
        )

        annotation_input = load_annotation_input(student_id)
        deepseek = load_deepseek_baseline(student_id)
        annotations = deepseek.get("annotations", {})  # {pid_str: {gaps: [...]}}

        # Collect all problems for this student with their assignment_id for ordering
        submissions_raw = annotation_input.get("submissions", {})
        problem_order = sorted(
            submissions_raw.keys(),
            key=lambda pid: (problem_assignment.get(int(pid), 9999), int(pid)),
        )

        for attempt_order, pid_str in enumerate(problem_order, start=1):
            pid = int(pid_str)
            sub_data = submissions_raw[pid_str]
            score = float(sub_data.get("score", 0.0))
            code = sub_data.get("code", "")

            # parse_status: ok for perfect-score (skipped), ok for successful parse
            parse_status = "ok"

            cursor = conn.execute(
                """INSERT INTO submissions
                   (student_id, problem_id, score, reasoning, code, parse_status, attempt_order, source)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'study')""",
                (student_id, pid, score, "", code, parse_status, attempt_order),
            )
            sub_id = cursor.lastrowid
            total_subs += 1

            # Gaps from DeepSeek annotation
            gaps = annotations.get(pid_str, {}).get("gaps", [])
            for kc in gaps:
                if kc in set(ALL_KCS):
                    conn.execute(
                        "INSERT OR IGNORE INTO submission_gaps (submission_id, kc) VALUES (?, ?)",
                        (sub_id, kc),
                    )
                    total_gaps += 1

        print(f"  Student {student_id} ({cluster}): {len(problem_order)} submissions")

    conn.commit()
    print(f"Inserted {total_subs} submissions, {total_gaps} gap rows")

    # --- 4. recurrence ---
    recurrence = compute_recurrence(cluster_map)
    for (kc, cluster), (hit_rate, n) in recurrence.items():
        if kc in set(ALL_KCS):
            conn.execute(
                "INSERT OR REPLACE INTO recurrence (kc, cluster, hit_rate, n) VALUES (?, ?, ?, ?)",
                (kc, cluster, hit_rate, n),
            )
    conn.commit()
    print(f"Inserted {len(recurrence)} recurrence rows (Gemini exp16 rates)")

    conn.close()
    print(f"\nDone. DB at {DB_PATH}")


if __name__ == "__main__":
    main()
