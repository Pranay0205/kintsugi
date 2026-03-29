"""Script to export one student's best-attempt code + score for each problem."""

from utils.dataset import get_best_attempts, load_joined_datasets
import argparse
import json
import os
import sys

import pandas as pd

# Allow running from project root
sys.path.append(os.getcwd())


try:
    from scripts.common_utils import DEFAULT_OUTPUT_DIR, ensure_output_dir
except ImportError:
    from common_utils import DEFAULT_OUTPUT_DIR, ensure_output_dir


def export_student_data(student_id, data_dir=DEFAULT_OUTPUT_DIR):
    """Export one student's best-attempt submissions as JSON."""

    ensure_output_dir(data_dir)

    print("Loading datasets using utils.dataset...")
    full_data = load_joined_datasets(verbose=False)
    if full_data is None:
        print("ERROR: Failed to load joined dataset.")
        return None

    print("Extracting best attempts...")
    best_attempts = get_best_attempts(full_data, verbose=False)

    # Filter to target student
    student_df = best_attempts[best_attempts['SubjectID'] == student_id].copy()

    if len(student_df) == 0:
        print(f"ERROR: No best attempts found for student {student_id}")
        return None

    print(f"Found {len(student_df)} best attempts for student {student_id}")

    # Build the JSON output keyed by ProblemID
    student_data = {}
    for _, row in student_df.iterrows():
        pid = str(int(row['ProblemID']))
        # Code column might be 'Code' or 'code'
        code = row.get('Code', row.get('code', ''))
        if pd.isna(code) or code == '':
            code = '// Code not available for this submission'

        student_data[pid] = {
            "code": code,
            "score": round(float(row['Score']), 6),
            "attempt": int(row['Attempt']) if pd.notna(row.get('Attempt')) else 0,
            "codeStateId": int(row['CodeStateID']) if pd.notna(row.get('CodeStateID')) else 0
        }

    # Save JSON
    output_file = os.path.join(data_dir, f"student_data_{student_id}.json")
    with open(output_file, 'w') as f:
        json.dump(student_data, f, indent=2)

    print(f"\nSaved to {output_file}")
    print(f"Problems exported: {len(student_data)}")

    # Show summary
    scores = [v['score'] for v in student_data.values()]
    perfect = sum(1 for s in scores if s >= 1.0)
    partial = sum(1 for s in scores if 0 < s < 1.0)
    zero = sum(1 for s in scores if s == 0)
    print(f"  Perfect (1.0): {perfect}")
    print(f"  Partial (0<s<1): {partial}")
    print(f"  Zero (0.0): {zero}")

    return output_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export student data for annotation tool")
    parser.add_argument("--student", type=int, required=True,
                        help="Student ID to export")
    parser.add_argument("--data-dir", type=str, default=DEFAULT_OUTPUT_DIR,
                        help="Directory to save output files")
    args = parser.parse_args()

    export_student_data(args.student, args.data_dir)
