"""Generate a combined per-student, per-problem HTML report showing student code
alongside Human A / Human B / V1-Baseline / V1-Enriched / V2-Baseline / V2-Enriched / V3
knowledge-gap tags, for the 10-student cohort used in exp19/exp20.
"""
import json
import os
import sys
from html import escape
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from utils.constants import PROBLEM_PROMPT_PATH

STUDENT_IDS = [
    '10155', '9948', '14189', '14352', '14362',
    '14363', '14374', '14414', '14474', '14499'
]

HUMAN_A_DIR = ROOT / 'dataset/Rater_KC_Tags/Rated_KC_V3'
HUMAN_B_DIR = ROOT / 'dataset/Rater_KC_Tags/Rated_KC_V3'
CODE_DIR = ROOT / 'scripts/annotation_tool/annotation_inputs'

EXP20_DIR = ROOT / 'results_consolidated/phase5_human_validation/exp20_v1_v2_on_10students'
EXP19_DIR = ROOT / 'results_consolidated/phase5_human_validation/exp19_v3_on_10students'

VARIANTS = {
    'V1_Baseline': EXP20_DIR / 'llm_v1_baseline_10students' / 'llm_v1_baseline_annotations_{sid}.json',
    'V1_Enriched': EXP20_DIR / 'llm_v1_enriched_10students' / 'llm_v1_enriched_annotations_{sid}.json',
    'V2_Baseline': EXP20_DIR / 'llm_v2_baseline_10students' / 'llm_v2_baseline_annotations_{sid}.json',
    'V2_Enriched': EXP20_DIR / 'llm_v2_enriched_10students' / 'llm_v2_enriched_annotations_{sid}.json',
    'V3': EXP19_DIR / 'llm_v3_10students' / 'llm_v3_annotations_{sid}.json',
}

OUT_DIR = ROOT / 'results_consolidated/phase5_human_validation/final_4way_prompt_evaluation'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def find_latest_file(directory, pattern):
    matches = sorted(directory.glob(pattern))
    return matches[-1] if matches else None


def load_annotation_map(filepath):
    """Load annotation JSON -> {problem_id_str: [gap KC strings]}."""
    if filepath is None or not Path(filepath).exists():
        return {}
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    annotations = {}
    for pid, val in data.get('annotations', {}).items():
        gaps = val.get('gaps', []) if isinstance(val, dict) else (val if isinstance(val, list) else [])
        cleaned = []
        for gap in gaps:
            gap_text = str(gap).strip()
            if gap_text and gap_text not in cleaned:
                cleaned.append(gap_text)
        annotations[str(pid)] = cleaned
    return annotations


def format_java_code(code):
    """Reindent Java source by brace depth and collapse runs of blank lines.

    Student submissions mix tabs/spaces and inconsistent indentation, and often
    contain several consecutive blank lines. This ignores the original
    whitespace and rebuilds it from brace nesting, which is enough for the
    simple CS1-level code in this dataset.
    """
    if not code:
        return code

    lines = [line.rstrip() for line in code.replace('\r\n', '\n').replace('\r', '\n').split('\n')]

    collapsed = []
    prev_blank = False
    for line in lines:
        is_blank = line.strip() == ''
        if is_blank and prev_blank:
            continue
        collapsed.append(line)
        prev_blank = is_blank
    while collapsed and collapsed[0].strip() == '':
        collapsed.pop(0)
    while collapsed and collapsed[-1].strip() == '':
        collapsed.pop()

    indent_level = 0
    indent_str = '    '
    out_lines = []
    for line in collapsed:
        stripped = line.strip()
        if stripped == '':
            out_lines.append('')
            continue
        leading_closers = len(stripped) - len(stripped.lstrip('}'))
        this_line_level = max(0, indent_level - leading_closers) if stripped.startswith('}') else indent_level
        out_lines.append(indent_str * this_line_level + stripped)
        indent_level = max(0, indent_level + stripped.count('{') - stripped.count('}'))

    return '\n'.join(out_lines)


def load_student_code(student_id):
    code_path = CODE_DIR / f"student_{student_id}.json"
    if not code_path.exists():
        return {}
    with open(code_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('submissions', {})


problem_prompts_df = pd.read_csv(PROBLEM_PROMPT_PATH)


def get_problem_meta(problem_id):
    row = problem_prompts_df[problem_prompts_df['ProblemID'] == int(problem_id)]
    if row.empty:
        return None, '(problem description unavailable)'
    item = row.iloc[0]
    aid = item.get('AssignmentID')
    aid = int(aid) if pd.notna(aid) else None
    return aid, str(item.get('Requirement', '(problem description unavailable)'))


# --- Load everything ---
RATER_KEYS = ['Human_A', 'Human_B'] + list(VARIANTS.keys())

all_data = {key: {} for key in RATER_KEYS}
all_student_code = {}

for sid in STUDENT_IDS:
    ha_file = find_latest_file(HUMAN_A_DIR, f"kc_annotations_Pranay Ghuge_{sid}_*.json")
    hb_file = find_latest_file(HUMAN_B_DIR, f"kc_annotations_Arundhati Das_{sid}_*.json")
    all_data['Human_A'][sid] = load_annotation_map(ha_file)
    all_data['Human_B'][sid] = load_annotation_map(hb_file)

    for variant, path_template in VARIANTS.items():
        variant_file = Path(str(path_template).format(sid=sid))
        all_data[variant][sid] = load_annotation_map(variant_file)

    all_student_code[sid] = load_student_code(sid)

# --- Build report rows (skip perfect scores) ---
report_rows = []
skipped_perfect = 0

for sid in STUDENT_IDS:
    submissions = all_student_code[sid]

    all_pids = set(submissions.keys())
    for key in RATER_KEYS:
        all_pids.update(all_data[key][sid].keys())

    for pid_str in sorted(all_pids, key=lambda x: int(x)):
        pid = int(pid_str)
        sub = submissions.get(pid_str, {})
        code = format_java_code(sub.get('code', ''))
        score = sub.get('score', None)

        if score is not None and score >= 1.0:
            skipped_perfect += 1
            continue

        assignment_id, requirement = get_problem_meta(pid)

        row = {
            'StudentID': sid,
            'ProblemID': pid,
            'AssignmentID': assignment_id,
            'Requirement': requirement,
            'Code': code,
            'Score': score,
        }
        for key in RATER_KEYS:
            row[key] = all_data[key][sid].get(pid_str)
        report_rows.append(row)

report_df = pd.DataFrame(report_rows)
report_df = report_df.sort_values(['StudentID', 'AssignmentID', 'ProblemID'], na_position='last').reset_index(drop=True)

print(f"Report rows: {len(report_df)}")
print(f"Skipped perfect-score: {skipped_perfect}")
print(f"Students: {report_df['StudentID'].nunique()}")

# --- Save CSV ---
def gaps_to_str(gaps):
    if gaps is None:
        return 'Missing'
    if len(gaps) == 0:
        return 'No gaps'
    return ', '.join(gaps)

csv_df = report_df.copy()
for key in RATER_KEYS:
    csv_df[key] = csv_df[key].apply(gaps_to_str)

csv_path = OUT_DIR / 'five_way_student_problem_rating_report.csv'
csv_df.to_csv(csv_path, index=False)
print(f"Saved CSV: {csv_path}")

# --- Build HTML ---
RATER_LABELS = {
    'Human_A': 'Human A',
    'Human_B': 'Human B',
    'V1_Baseline': 'V1 Baseline',
    'V1_Enriched': 'V1 Enriched',
    'V2_Baseline': 'V2 Baseline',
    'V2_Enriched': 'V2 Enriched',
    'V3': 'V3',
}


def render_code_block(code):
    text = code if code else '(no code found)'
    return f"<pre class='student-code'><code>{escape(text)}</code></pre>"


def render_gap_badges(gaps):
    if gaps is None:
        return "<span class='gap-empty'>Missing</span>"
    if len(gaps) == 0:
        return "<span class='gap-empty'>No gaps</span>"
    badges = ''.join(f"<span class='gap-badge'>{escape(gap)}</span>" for gap in gaps)
    return f"<div class='gap-badge-wrap'>{badges}</div>"


def agreement_indicator(row):
    sets = {}
    for key in RATER_KEYS:
        gaps = row[key]
        if gaps is None:
            return "<span class='agree-unknown'>?</span>"
        sets[key] = frozenset(gaps)
    unique_sets = set(sets.values())
    if len(unique_sets) == 1:
        return "<span class='agree-all'>All Agree</span>"
    ha_hb_agree = sets['Human_A'] == sets['Human_B']
    if ha_hb_agree:
        return "<span class='agree-hh'>H-H Agree, LLM(s) Differ</span>"
    return "<span class='agree-none'>Mixed</span>"


html_parts = [
    "<style>",
    "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }",
    ".report-wrap { max-width: 1200px; margin: 0 auto; }",
    ".report-title { font-size: 1.6rem; font-weight: 800; margin-bottom: 0.5rem; }",
    ".report-subtitle { font-size: 1rem; color: #6b7280; margin-bottom: 1.5rem; }",
    ".student-card { border: 2px solid #e5e7eb; border-radius: 12px; padding: 0; margin: 1.2rem 0; overflow: hidden; }",
    ".student-card > summary { cursor: pointer; font-size: 1.15rem; font-weight: 700; padding: 0.8rem 1rem; background: #f9fafb; border-bottom: 1px solid #e5e7eb; }",
    ".student-card > summary:hover { background: #f3f4f6; }",
    ".problem-card { margin: 0; border-top: 1px solid #f3f4f6; padding: 0.8rem 1rem; }",
    ".problem-card:hover { background: #fafbfc; }",
    ".problem-card > summary { cursor: pointer; font-size: 0.95rem; font-weight: 600; color: #1f2937; display: flex; justify-content: space-between; align-items: center; }",
    ".problem-desc { white-space: pre-wrap; line-height: 1.55; color: #374151; margin-top: 0.5rem; font-size: 0.9rem; background: #f9fafb; padding: 0.6rem 0.8rem; border-radius: 8px; }",
    ".student-code { margin: 0.5rem 0; padding: 0.7rem 0.9rem; border-radius: 8px; background: #1e1e2e; color: #cdd6f4; overflow: auto; white-space: pre; font-size: 0.85rem; line-height: 1.45; font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace; max-height: 600px; }",
    ".gap-badge-wrap { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.2rem; }",
    ".gap-badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 999px; background: #dbeafe; color: #1d4ed8; font-size: 0.78rem; font-weight: 600; }",
    ".gap-empty { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 999px; background: #f3f4f6; color: #9ca3af; font-size: 0.78rem; font-weight: 600; }",
    ".rating-table { width: 100%; border-collapse: collapse; margin-top: 0.5rem; font-size: 0.88rem; }",
    ".rating-table th, .rating-table td { border: 1px solid #e5e7eb; padding: 0.45rem 0.6rem; vertical-align: top; text-align: left; }",
    ".rating-table th { background: #f9fafb; width: 15%; font-weight: 600; }",
    ".agree-all { background: #d1fae5; color: #065f46; padding: 0.15rem 0.5rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }",
    ".agree-hh { background: #fee2e2; color: #991b1b; padding: 0.15rem 0.5rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }",
    ".agree-none { background: #f3f4f6; color: #6b7280; padding: 0.15rem 0.5rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }",
    ".agree-unknown { background: #f3f4f6; color: #9ca3af; padding: 0.15rem 0.5rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }",
    "</style>",
    "<div class='report-wrap'>",
    "<div class='report-title'>5-Way Rating Report: Human A / Human B / V1 / V2 / V3</div>",
    f"<div class='report-subtitle'>10 struggling students &middot; {len(report_df)} non-perfect problems &middot; "
    f"7 raters (Human A, Human B, V1 Baseline, V1 Enriched, V2 Baseline, V2 Enriched, V3)</div>",
]

for sid in STUDENT_IDS:
    student_df = report_df[report_df['StudentID'] == sid]
    if student_df.empty:
        continue

    n_problems = len(student_df)
    n_all_agree = sum(
        1 for _, row in student_df.iterrows()
        if all(row[k] is not None for k in RATER_KEYS)
        and len({frozenset(row[k]) for k in RATER_KEYS}) == 1
    )

    html_parts.append(
        f"<details class='student-card'>"
        f"<summary>Student {sid} &mdash; {n_problems} problems (All 7 raters agree: {n_all_agree})</summary>"
    )

    for _, row in student_df.sort_values(['AssignmentID', 'ProblemID'], na_position='last').iterrows():
        pid = int(row['ProblemID'])
        assignment_text = f"Assignment {int(row['AssignmentID'])}" if pd.notna(row['AssignmentID']) else 'Assignment ?'
        score_text = f"{row['Score']:.3f}" if row['Score'] is not None else '?'

        agree_badge = agreement_indicator(row)

        rating_rows = ''.join(
            f"<tr><th>{RATER_LABELS[key]}</th><td>{render_gap_badges(row[key])}</td></tr>"
            for key in RATER_KEYS
        )

        html_parts.append(
            f"<details class='problem-card'>"
            f"<summary>"
            f"<span>Problem {pid} &mdash; {escape(assignment_text)} &mdash; Score: {score_text}</span>"
            f"{agree_badge}"
            f"</summary>"
            f"<div class='problem-desc'><strong>Problem:</strong> {escape(str(row['Requirement']))}</div>"
            f"<div style='margin-top:0.5rem'><strong>Student Code:</strong>{render_code_block(str(row['Code']))}</div>"
            f"<table class='rating-table'><tbody>{rating_rows}</tbody></table>"
            f"</details>"
        )

    html_parts.append('</details>')

html_parts.append('</div>')
report_html = '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>5-Way Rating Report</title></head><body>' + ''.join(html_parts) + '</body></html>'

html_path = OUT_DIR / 'five_way_student_problem_rating_report.html'
html_path.write_text(report_html, encoding='utf-8')
print(f"Saved HTML: {html_path}")
