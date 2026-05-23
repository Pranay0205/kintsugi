# Exp 4b — Corrected F1 Metric

- **Date:** 2026-03-23
- **Phase:** 2 (Mental model) · V1 correction
- **Notebook:** [exp4b_corrected_f1_metric.ipynb](../../../experiments/phase2_mental_model/exp4b_corrected_f1_metric.ipynb)
- **Status:** ✓ Supersedes exp4's headline numbers. Notebook has no cell outputs; CSVs were written but the notebook itself needs a rerun to embed visuals.

## Question
Does enrichment still win after fixing the F1 metric to score only on weak skills the problem actually tests (`testable_weak = student_weak ∩ problem_required`)?

## Method
- Re-reads exp4's batch CSV (no new LLM calls)
- Recomputes F1 on `testable_weak` ground truth only
- Of 330 rows, only **58 have any testable weak skill** — the corrected metric throws out 82% of rows as undefined.

## Key result (recovered from saved CSV)
| | Corrected Baseline F1 | Corrected Enriched F1 | Δ |
|---|---|---|---|
| Overall | 0.332 | 0.372 | +0.040 |
| Struggling (n=49) | — | — | +0.034 |
| Average (n=9) | — | — | +0.075 |
| High Performer | — | — | (no testable rows) |

- Win rate: 9/13 students with any weak skill.
- **Bottom line:** enrichment effect is real but modest (~+0.04 F1); the old metric was inflated by counting non-testable skills in the denominator.

## Files
- `batch_comparison_30students_corrected.csv` — recomputed per-row scores
- `per_student_summary_corrected.csv` — corrected per-student aggregates
