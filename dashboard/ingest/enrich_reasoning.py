"""
Backfill study submissions with reasoning from existing Gemini V3 annotation files.

Primary source: results/human_validation/llm_v3_10students/llm_v3_annotations_{student_id}.json
These contain full reasoning from Gemini 2.5 Flash V3 (produced during the study).
Fallback: calls DeepSeek API (DEEPSEEK_API_KEY) for any submission not covered.

Usage:
    python enrich_reasoning.py [--dry-run] [--limit N]
    DEEPSEEK_API_KEY=<key> python enrich_reasoning.py   # enables DeepSeek fallback
"""

import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from lib.v3_prompt import build_v3_prompt

DB_PATH = Path(__file__).resolve().parent.parent / "kintsugi.db"
V3_DIR  = REPO / "results" / "human_validation" / "llm_v3_10students"

ALL_KCS = {
    "If/Else", "NestedIf", "While", "For", "NestedFor",
    "Math+-*/", "Math%", "LogicAndNotOr", "LogicCompareNum", "LogicBoolean",
    "StringFormat", "StringConcat", "StringIndex", "StringLen",
    "StringEqual", "CharEqual", "ArrayIndex", "DefFunction",
}

# ---------------------------------------------------------------------------
# Load existing Gemini V3 reasoning from files
# ---------------------------------------------------------------------------

def load_gemini_v3() -> dict[tuple[int, int], str]:
    """Returns {(student_id, problem_id): reasoning}."""
    index: dict[tuple[int, int], str] = {}
    for path in V3_DIR.glob("llm_v3_annotations_*.json"):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        sid = int(data.get("student_id", 0))
        for pid_str, entry in data.get("raw_responses", {}).items():
            parsed = entry.get("parsed_response", {})
            reasoning = parsed.get("reasoning", "")
            if reasoning:
                index[(sid, int(pid_str))] = reasoning
    return index


# ---------------------------------------------------------------------------
# Pending submissions
# ---------------------------------------------------------------------------

def load_pending(conn: sqlite3.Connection, limit: int | None) -> list[dict]:
    sql = """
        SELECT sub.id, sub.student_id, sub.problem_id, sub.score, sub.code,
               p.requirement, p.assignment_id
        FROM submissions sub
        JOIN problems p ON p.id = sub.problem_id
        WHERE sub.source = 'study'
          AND sub.reasoning = ''
          AND sub.score < 1.0
          AND EXISTS (SELECT 1 FROM submission_gaps sg WHERE sg.submission_id = sub.id)
        ORDER BY sub.id
    """
    if limit:
        sql += f" LIMIT {limit}"
    cur = conn.execute(sql)
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    problem_kcs: dict[int, list[str]] = {}
    for row in rows:
        pid = row["problem_id"]
        if pid not in problem_kcs:
            problem_kcs[pid] = [r[0] for r in conn.execute(
                "SELECT kc FROM problem_kcs WHERE problem_id = ?", (pid,)
            ).fetchall()]
        row["required_kcs"] = problem_kcs[pid]
    return rows


# ---------------------------------------------------------------------------
# DeepSeek fallback
# ---------------------------------------------------------------------------

def call_deepseek(prompt: str) -> tuple[str, str]:
    """Returns (reasoning, parse_status)."""
    import urllib.request

    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        return "", "no_api_key"

    payload = json.dumps({
        "model": "deepseek-chat",
        "temperature": 0.3,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            body = json.loads(resp.read())
    except Exception as e:
        print(f"  DeepSeek error: {e}", file=sys.stderr)
        return "", "api_error"

    content = body["choices"][0]["message"]["content"].strip()
    if content.startswith("```"):
        lines = content.split("\n", 1)
        content = lines[1] if len(lines) > 1 else content
        if "```" in content:
            content = content[:content.rfind("```")]
        content = content.strip()
    try:
        obj = json.loads(content)
        return obj.get("reasoning", ""), "ok"
    except json.JSONDecodeError:
        return content, "parse_error"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    print("Loading existing Gemini V3 reasoning from llm_v3_10students/...")
    gemini_index = load_gemini_v3()
    print(f"  Found reasoning for {len(gemini_index)} (student, problem) pairs")

    conn = sqlite3.connect(DB_PATH)
    pending = load_pending(conn, args.limit)

    if not pending:
        print("Nothing to backfill — all reasoning already populated.")
        conn.close()
        return

    print(f"\nBackfilling {len(pending)} submissions...")

    from_gemini = 0
    from_deepseek = 0
    skipped = 0

    for i, row in enumerate(pending, 1):
        sid, pid = row["student_id"], row["problem_id"]
        label = f"[{i}/{len(pending)}] submission {row['id']} (student {sid}, problem {pid}, score {row['score']:.2f})"

        # Primary: use existing Gemini V3 result
        reasoning = gemini_index.get((sid, pid), "")
        source = "gemini_v3"

        if not reasoning:
            # Fallback: DeepSeek API
            if not os.environ.get("DEEPSEEK_API_KEY"):
                print(f"  {label} — no Gemini result, DEEPSEEK_API_KEY not set, skipping")
                skipped += 1
                continue

            print(f"  {label} — calling DeepSeek (not in Gemini V3 results)")
            if not args.dry_run:
                prompt = build_v3_prompt(
                    problem_id=pid,
                    requirement=row["requirement"],
                    assignment_id=row["assignment_id"],
                    required_kcs=row["required_kcs"],
                    student_code=row["code"],
                    score=row["score"],
                )
                reasoning, status = call_deepseek(prompt)
                if status != "ok" or not reasoning:
                    skipped += 1
                    continue
                from_deepseek += 1
                time.sleep(1.2)
            source = "deepseek"
        else:
            from_gemini += 1

        print(f"  {label} [{source}]: {reasoning[:80]}...")

        if not args.dry_run:
            conn.execute("UPDATE submissions SET reasoning = ? WHERE id = ?", (reasoning, row["id"]))
            conn.commit()

    conn.close()
    print(f"\nDone. Gemini: {from_gemini}  DeepSeek: {from_deepseek}  Skipped: {skipped}")


if __name__ == "__main__":
    main()
