# Exp 18 — Per-KC Power-Law Learning Curves

- **Date:** 2026-05-05
- **Phase:** 5 (Human validation) · ⚠ exploratory, half-executed
- **Notebook:** [exp18_kc_learning_curves.ipynb](../../../experiments/phase5_human_validation/exp18_kc_learning_curves.ipynb)
- **Status:** ⚠ Fits are degenerate (b ≈ 0); cells 6–9 not executed. Recommend cutting from thesis or rebuilding.

## Question
Do per-KC scores follow a power-law learning curve, and does the V3 gap-rate decay better than a problem-score baseline?

## Method
- 28 students, 9 fit-eligible KCs (≥10 problems each)
- 9 KCs excluded for too few problems (While, Math%, DefFunction, NestedFor, …)
- 4,377 timeline rows; constrained power-law `a * x^b` fit per-student (442 fits) and aggregate (18 fits)
- Also: early/mid/late binned gap-rate analysis

## Key result
- Fits ran and CSVs were written, **but the fitted `b` exponents are essentially zero** (e.g. student 10155 If/Else baseline `b = -3.5e-12`, v3 `b = 0`). No actual learning trajectory recovered — curves are flat.
- Notebook executed only through cell 5/8; binned gap-rate analysis and plotting (cells 6–9) have no executed outputs.

## Files
- `exp18_kc_aggregate_curves.csv` — aggregate fits
- `exp18_kc_fit_metrics.csv` — per-fit RMSE/R²
- `exp18_kc_timeline_data.csv` — raw timeline (4,377 rows)
- `exp18_learning_curve_summary.json`, `exp18_gap_rate_summary.json` — summary stats
- `exp18_visualizations/` — partial figures
