# Final 4-Way Prompt Evaluation (V1/V2 baseline+enriched, V3)

- **Phase:** 5 (Human validation) · **final eval on the 10-struggling-student cohort**
- **Inputs:** annotations from [exp19](../exp19_v3_on_10students/) (V3) and [exp20](../exp20_v1_v2_on_10students/) (V1/V2 baseline+enriched), evaluated against 2 human raters (372 common annotations)
- **Status:** ✓ This is the consolidated headline evaluation for the thesis.

## What's here

Two evaluation runs over the same 10-student cohort:

### `all_prompts/` — 4-way (5-way with V3) prompt comparison
- `all_prompts_eval_summary.json` — top-level summary numbers
- `all_prompts_headline.csv` — headline metrics per prompt
- `all_prompts_ranking.csv` — prompts ranked by performance
- `all_prompts_summary.csv` — full per-prompt summary
- `all_prompts_detail.csv` — per-(student, problem) breakdown

### `v3_eval/` — V3-only deep dive
- `v3_prompt_eval_summary.json` — top-level summary
- `overall_metrics.csv` — overall κ/F1/precision/recall
- `per_student_metrics.csv` — per-student breakdown
- `per_kc_pair_metrics.csv` — per-KC, per rater-pair breakdown
- `per_kc_ceiling_metrics.csv` / `ceiling_metrics.csv` — comparison against human-human ceiling
- `problem_level_metrics.csv` / `problem_level_summary.json` — per-problem stats

## How to read
Start with `all_prompts/all_prompts_ranking.csv` for the top-line "which prompt wins" answer. Use `v3_eval/ceiling_metrics.csv` to see how close V3 gets to the human-rater ceiling. Per-KC tables surface which KCs the LLM still tags inconsistently.
