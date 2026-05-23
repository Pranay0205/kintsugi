# Exp 16 — Learning Curve on 30 (actually 28) Students

- **Date:** 2026-04-27 (+ visualizations 2026-04-28)
- **Phase:** 5 (Human validation) · ⚠ exploratory but methodologically the strongest of the LC batch
- **Notebooks:**
  - [exp16_learning_curve_30students.ipynb](../../../experiments/phase5_human_validation/exp16_learning_curve_30students.ipynb)
  - [exp16_learning_curve_visualizations.ipynb](../../../experiments/phase5_human_validation/exp16_learning_curve_visualizations.ipynb)
  - [exp16_student_problem_rating_report.ipynb](../../../experiments/phase5_human_validation/exp16_student_problem_rating_report.ipynb)
- **Status:** Cluster-conditional result is real but the headline aggregate (58.4%) is **misleading on its own** — it's carried entirely by the struggling cluster.

## Question
Does the V3 predictive-validity result (exp15) hold at scale across clusters?

## Method
- Same temporal-next-problem TP/FP method as exp15
- 28 students (cohort labeled "30students"): 10 Average, 10 High Performer, 8 Struggling
- V3 annotation via Gemini on all non-perfect problems (~250 API calls)

## Key result
- 226 validatable predictions: 132 TP / 94 FP = **58.4% hit rate**
- Random baseline: **26.4% ± 2.8%** (beats random by > 3σ)

| Cluster | Hit rate | n |
|---|---|---|
| **Struggling** | **77.0%** | 148 |
| Average | 26.5% | 68 |
| High Performer | 0.0% | 10 |

- The signal is **almost entirely from struggling students.** High Performer predictions are essentially all false positives.
- Visualizations show 16 students with any validatable predictions (not all 28).

## Files
- `exp16_learning_curve_30students.json` — full results
- `exp16_per_student_summary_30students.csv` — per-student summary
- `exp16_predictions_30students.csv` — per-prediction TP/FP
- `exp16_checkpoint_30students.json` — incremental checkpoint
- `exp16_visualizations/` — cluster bar, per-student bar, KC×Cluster heatmaps
- `llm_v3_lc_*.json` — per-student V3 annotations used for the LC analysis
- `v3_predictions.csv` — predictions table
- `exp16_student_problem_rating_report.{csv,html}` — qualitative per-(student, problem) review (3 pilot students, 73 rows)
