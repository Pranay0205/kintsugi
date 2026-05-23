# Exp 11 — V2 Baseline & Enriched vs Human (3 students)

- **Date:** 2026-04-10
- **Phase:** 5 (Human validation) · V2 final numbers (3-student pilot cohort)
- **Notebooks:**
  - [exp11_baseline_vs_human.ipynb](../../../experiments/phase5_human_validation/exp11_baseline_vs_human.ipynb)
  - [exp11_enriched_vs_human.ipynb](../../../experiments/phase5_human_validation/exp11_enriched_vs_human.ipynb)
- **Status:** ✓ Final V2 numbers on 3-student pilot. Notable negative result: **mental model hurts V2 performance.**

## Question
Does the V2 (difficulty-weighted) curriculum-aware prompt improve over V1? Does adding the mental model help on V2?

## Method
- Same 3 students, n = 146 common problems
- V2 baseline: `build_curriculum_aware_prompt_v2` (no mental model)
- V2 enriched: V2 prompt + `add_mental_model_context`

## Key result
| Rater | Cohen's κ | F1 |
|---|---|---|
| Human A vs Human B | 0.421 | 0.459 |
| **V2 Baseline (avg)** | **0.371** | **0.412** |
| V2 Enriched (avg) | 0.354 | 0.396 |
| V1 Baseline (for reference) | 0.300 | 0.352 |
| V1 Enriched (for reference) | 0.321 | 0.359 |

Per-rater splits:
- V2 Baseline: HA = 0.470 · HB = 0.273
- V2 Enriched: HA = 0.449 · HB = 0.258

- **V2 beats V1** on every variant.
- **V2 Baseline > V2 Enriched** — mental model adds noise rather than signal at V2. This is a real negative result.

## Files
- `exp11_baseline_v2_vs_human_metrics.json` — V2 baseline metrics
- `exp11_enriched_v2_vs_human_metrics.json` — V2 enriched metrics
- `llm_baseline_annotations_v2_{10155,14475,14476}.json` — V2 baseline annotations
- `llm_enriched_annotations_v2_{10155,14475,14476}.json` — V2 enriched annotations
