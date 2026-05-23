# Exp 20 — V1 & V2 (Baseline + Enriched) on the 10-Student Cohort

- **Date:** 2026-05-21
- **Phase:** 5 (Human validation) · **final eval input — V1/V2 side**
- **Notebook:** [exp20_v1_v2_annotation.ipynb](../../../experiments/phase5_human_validation/exp20_v1_v2_annotation.ipynb)
- **Status:** ✓ All 4 variants confirmed present on disk (10 files each). Enables the fair 4-way comparison in [final_4way_prompt_evaluation](../final_4way_prompt_evaluation/).

## Question
Generate V1-baseline, V1-enriched, V2-baseline, V2-enriched annotations on the same 10 students used in exp19, so that all 4 (or 5 with V3) prompt variants can be compared apples-to-apples against the same human-rater ground truth.

## Method
- Parametrized notebook with `PROMPT_VARIANT` toggle (run 4 times, one per variant)
- Same per-problem API pattern as exp19 (Gemini 2.5 Flash, T = 0.3, skip perfect scores)
- Mental model built via `lib/mental_model.py` for enriched variants
- KC tags extracted **only from `student_analysis[].knowledge_gaps[].missing_concept`** (not future predictions) — matches human-rater semantics

## Key result
- `v2_enriched` last-run from saved cell outputs: **188 calls, 149 problems with gaps, 0 errors.** Per-student gap counts: 21, 12, 18, 15, 7, 11, 23, 15, 15, 12.
- All 4 variant directories verified on disk with the full 10-student set.

## Files
- `llm_v1_baseline_10students/` — V1 baseline annotations (10 students)
- `llm_v1_enriched_10students/` — V1 enriched annotations (10 students)
- `llm_v2_baseline_10students/` — V2 baseline annotations (10 students)
- `llm_v2_enriched_10students/` — V2 enriched annotations (10 students)
