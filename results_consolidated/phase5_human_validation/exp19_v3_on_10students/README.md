# Exp 19 — V3 (CCPP) Annotation on the 10-Struggling-Student Cohort

- **Date:** 2026-05-05
- **Phase:** 5 (Human validation) · **final eval input — V3 side**
- **Notebook:** [exp19_llm_v3_annotation.ipynb](../../../experiments/phase5_human_validation/exp19_llm_v3_annotation.ipynb)
- **Status:** ✓ Eval-ready V3 dataset for the final cohort. Feeds [final_4way_prompt_evaluation](../final_4way_prompt_evaluation/).

## Question
Run V3 / CCPP on the final 10-struggling-student cohort to enable a head-to-head comparison against humans (and against V1/V2 from exp20).

## Method
- Gemini 2.5 Flash, temperature 0.3
- V3 prompt (no mental model)
- Per-submission API calls (one problem per call); perfect scores skipped client-side
- 10 students: 10155, 9948, 14189, 14352, 14362, 14363, 14374, 14414, 14474, 14499

## Key result
- **188 API calls, 126 problems with gaps flagged, 0 errors.**
- Per-student gap counts: 12, 9, 15, 14, 7, 10, 22, 15, 12, 10.
- Sanity check vs Human A on 10155 shows partial overlap (e.g. P22 both flag DefFunction & LogicCompareNum; LLM swaps LogicBoolean → LogicAndNotOr).

## Files
- `llm_v3_10students/llm_v3_annotations_<sid>.json` — per-student V3 annotations (10 files)
- `exp19_student_problem_rating_report.{csv,html}` — qualitative side-by-side review
- `exp19_three_way_comparison.csv` — human A / human B / V3 comparison table
- `exp19_visualizations/` — figures
