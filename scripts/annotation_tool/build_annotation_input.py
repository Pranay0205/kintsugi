#!/usr/bin/env python3
"""
Build per-student annotation input files for kc_annotation_tool_v2.html.

Usage:
    python build_annotation_input.py \
        --main dataset/CodeWorkout/MainTable.csv \
        --codestate dataset/CodeWorkout/LinkTables/CodeState.csv \
        --students 10155,14374,14189,14499,14362,14352,14474,14414,9948,14363 \
        --out annotation_inputs/

Output format (one file per student):
    {
      "studentId": "10155",
      "submissions": {
        "13": { "code": "...", "score": 0.78 },
        "24": { "code": "...", "score": 0.0 },
        ...
      }
    }

Best-attempt selection: highest Score per (SubjectID, ProblemID). Ties broken by
highest Attempt number (later attempt wins). Only Run.Program events are
considered — Compile and Compile.Error rows are ignored.
"""

import argparse
import json
from pathlib import Path

import pandas as pd


def load_codestate(path):
    """Load CodeState.csv as a {CodeStateID: code} dict."""
    df = pd.read_csv(path, dtype={"CodeStateID": int, "Code": str})
    return dict(zip(df["CodeStateID"], df["Code"]))


def load_main(path, student_ids):
    """Load MainTable.csv filtered to the target students and Run.Program events."""
    # Read only the columns we need; dtype=str avoids mixed-type warnings on large file
    usecols = ["SubjectID", "ProblemID", "Attempt", "CodeStateID", "EventType", "Score"]
    df = pd.read_csv(path, usecols=usecols, dtype=str)

    # Filter to target students (as strings — SubjectID may be int-like)
    student_ids_str = {str(s) for s in student_ids}
    df = df[df["SubjectID"].isin(student_ids_str)]

    # Only Run.Program rows carry scores
    df = df[df["EventType"] == "Run.Program"].copy()

    # Types
    df["SubjectID"] = df["SubjectID"].astype(int)
    df["ProblemID"] = df["ProblemID"].astype(int)
    df["Attempt"] = df["Attempt"].astype(int)
    df["CodeStateID"] = df["CodeStateID"].astype(int)
    df["Score"] = pd.to_numeric(df["Score"], errors="coerce")
    df = df.dropna(subset=["Score"])

    return df


def pick_best_attempts(df):
    """For each (SubjectID, ProblemID), pick the row with highest Score, ties broken by highest Attempt."""
    df = df.sort_values(["SubjectID", "ProblemID", "Score", "Attempt"],
                        ascending=[True, True, False, False])
    return df.groupby(["SubjectID", "ProblemID"], as_index=False).first()


def build_student_payload(student_id, best_df, codestate_map, reference_map):
    """Assemble one student's JSON payload."""
    rows = best_df[best_df["SubjectID"] == student_id]
    submissions = {}
    missing_code = 0
    for _, row in rows.iterrows():
        code = codestate_map.get(row["CodeStateID"])
        if code is None:
            missing_code += 1
            continue
        pid_str = str(row["ProblemID"])
        entry = {
            "code": code,
            "score": float(row["Score"]),
        }
        ref = reference_map.get(pid_str)
        if ref:
            entry["solution1"] = ref.get("solution1", "")
            entry["solution2"] = ref.get("solution2", "")
        submissions[pid_str] = entry
    return {
        "studentId": str(student_id),
        "submissions": submissions,
    }, len(rows), missing_code


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--main", required=True, help="Path to MainTable.csv")
    ap.add_argument("--codestate", required=True, help="Path to CodeState.csv")
    ap.add_argument("--students", required=True, help="Comma-separated SubjectIDs")
    ap.add_argument("--out", required=True, help="Output directory for per-student JSON files")
    ap.add_argument("--references", default=None,
                    help="Optional path to reference_solutions.json to merge into each student file")
    args = ap.parse_args()

    student_ids = [int(s.strip()) for s in args.students.split(",") if s.strip()]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading CodeState from {args.codestate} ...")
    codestate_map = load_codestate(args.codestate)
    print(f"  {len(codestate_map):,} code snippets loaded")

    reference_map = {}
    if args.references:
        print(f"Loading reference solutions from {args.references} ...")
        with open(args.references, "r", encoding="utf-8") as f:
            reference_map = json.load(f)
        print(f"  {len(reference_map):,} reference solution entries loaded")
    else:
        print("No reference-solutions file provided; student files will omit solution1/solution2.")

    print(f"Loading MainTable from {args.main} (filtering to {len(student_ids)} students) ...")
    main_df = load_main(args.main, student_ids)
    print(f"  {len(main_df):,} Run.Program rows for target students")

    print("Picking best attempt per (student, problem) ...")
    best_df = pick_best_attempts(main_df)
    print(f"  {len(best_df):,} best-attempts selected")

    print("\nBuilding per-student payloads:")
    print(f"  {'SubjectID':>10}  {'#Problems':>10}  {'#Missing':>10}  Output")
    for sid in student_ids:
        payload, n_rows, n_missing = build_student_payload(sid, best_df, codestate_map, reference_map)
        if not payload["submissions"]:
            print(f"  {sid:>10}  {'(no data)':>10}  {'-':>10}  SKIPPED")
            continue
        out_path = out_dir / f"student_{sid}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"  {sid:>10}  {n_rows:>10}  {n_missing:>10}  {out_path}")

    print(f"\nDone. Files in {out_dir.resolve()}/")


if __name__ == "__main__":
    main()
