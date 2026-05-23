# Exp 12 — V3 (CCPP) vs Human (3 students)

- **Date:** 2026-04-24 (+ visualizations 2026-04-28)
- **Phase:** 5 (Human validation) · **V3 / CCPP — headline thesis claim (3-student pilot)**
- **Notebooks:**
  - [exp12_v3_prompt_experiment.ipynb](../../../experiments/phase5_human_validation/exp12_v3_prompt_experiment.ipynb)
  - [exp12_v3_human_llm_agreement_visualizations.ipynb](../../../experiments/phase5_human_validation/exp12_v3_human_llm_agreement_visualizations.ipynb)
- **Status:** ⚠ First V3 numbers, but with a methodological caveat (denominator differs from V1/V2). Re-run on the 10-student cohort is [exp19](../exp19_v3_on_10students/) + [final_4way_prompt_evaluation](../final_4way_prompt_evaluation/).

## Question
Does V3 (per-problem CCPP prompt with required-KC scaffolding + score gating) beat V1 and V2?

## Method
- 3 students, V3 prompt run per problem (Gemini 2.5 Flash)
- **Skips perfect-score / trivial code submissions** client-side
- Comparison done on **non-empty problems only (n = 44)**, not the n=146 used in exp10/exp11

## Key result (V3 row computed on n=44)
| Prompt | Cohen's κ | F1 | n |
|---|---|---|---|
| V1 Baseline | 0.300 | 0.352 | 146 |
| V2 Baseline | 0.371 | 0.412 | 146 |
| **V3 (CCPP)** | **0.447** | **0.532** | 44 |

- **V3 is the best by κ and F1.**
- ⚠ **Caveat:** the V3 vs V1/V2 table mixes denominators. V3 is on n=44 (non-empty filter); V1/V2 numbers reused from exp10/11 are on n=146. This is not strictly apples-to-apples. The clean re-run is in [final_4way_prompt_evaluation](../final_4way_prompt_evaluation/).
- Per-KC V3 κ: best on CharEqual (0.836), Math% (0.734), StringConcat (0.658); weakest on If/Else (0.088), LogicCompareNum (0.108), NestedIf (0). Several KCs return NaN (While, NestedFor) — no positive cases.

## Files
- `exp12_v3_vs_human_metrics.json` — V3 vs human summary (n=44)
- `exp14_v3_vs_human_metrics.json` — supplementary V3 vs human metrics
- `llm_v3_annotations_{10155,14475,14476}.json` — V3 annotations on 3 students
- `v3_human_annotated_results.csv` — joined per-problem comparison
- `v3_per_kc_metrics.csv` — per-KC κ/F1 breakdown
- `exp12_visualizations/` — problem × KC heatmaps (3 PNGs)
