# Exp 10 — V1 Baseline & Enriched vs Human (3 students)

- **Date:** 2026-04-03 / 2026-04-10
- **Phase:** 5 (Human validation) · V1 final numbers (3-student pilot cohort)
- **Notebooks:**
  - [exp10a_baseline_vs_human.ipynb](../../../experiments/phase5_human_validation/exp10a_baseline_vs_human.ipynb)
  - [exp10b_enriched_vs_human.ipynb](../../../experiments/phase5_human_validation/exp10b_enriched_vs_human.ipynb)
- **Status:** ✓ Final V1 numbers on the 3-student pilot cohort. Re-run on the 10-student final cohort lives in [exp20](../exp20_v1_v2_on_10students/).

## Question
How does V1 curriculum-aware (baseline, no mental model) compare to V1 + mental model and to humans?

## Method
- 3 students (10155 struggling, 14475 high-perf, 14476)
- n = 146 common problems (all common, no empty-problem filter)
- Metrics: Cohen's κ, F1 averaged across both human raters

## Key result
| Rater | Cohen's κ | F1 |
|---|---|---|
| Human A vs Human B | **0.421** | 0.459 |
| V1 Baseline (avg) | 0.300 | 0.352 |
| V1 Enriched (avg) | 0.321 | 0.359 |

Per-rater splits:
- V1 Baseline: HA = 0.383 · HB = 0.217
- V1 Enriched: HA = 0.417 · HB = 0.225

- Mental model gives only marginal lift (~+0.02 κ).
- Arundhati (HB) systematically tags more KCs → lower agreement with the LLM regardless of variant.
- exp10b adds a KC-level disagreement report: highest disagreement on If/Else (28.8%), LogicCompareNum (26.7%), LogicAndNotOr (25.3%). Reaches **76.3% of human baseline** on average vs LLM.

## Files
- `exp10_baseline_vs_human_metrics.json` — V1 baseline metrics
- `human_validation_results_9files.json` — V1 enriched analytical companion
- `llm_baseline_annotations_{10155,14475,14476}.json` — V1 baseline annotations
- `llm_annotations_{10155,14475,14476}.json` — V1 enriched annotations
