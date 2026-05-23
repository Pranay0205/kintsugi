# Exp 15 — Learning Curve Validation (pilot)

- **Date:** 2026-04-24
- **Phase:** 5 (Human validation) · ⚠ exploratory pilot
- **Notebook:** [exp15_learning_curve_validation.ipynb](../../../experiments/phase5_human_validation/exp15_learning_curve_validation.ipynb)
- **Status:** Pilot for exp16. Tiny sample, dominated by 2 struggling students.

## Question
Do V3-flagged KC gaps predict struggle on the next problem requiring that KC?

## Method
- 3 students (10155, 14476, 14475)
- For each problem with a V3 gap tag, find the next temporally-ordered problem requiring that KC
- TP if the future score < 1.0; FP otherwise
- Random baseline via 1000 trials

## Key result
- 97 validatable predictions: 76 TP / 21 FP = **78.4% hit rate**
- Random baseline: **51.2%** (+27.1 pp over random)
- At threshold 0.8: 69.1%
- Per-student wildly variable: 84.2% / 82.7% / 14.3% (last student had only 7 validatable cases)

## Files
- `exp15_learning_curve_summary.json` — summary stats
- `exp15_learning_curve_curves.png`, `exp15_learning_curve_kc_hit_rates.png`, `exp15_learning_curve_powerlaw.png`, `exp15_learning_curve_student_outcomes.png` — curves
- `exp15_kc_link_diagram_10155.png`, `exp15_kc_link_diagram_all_students.png` — KC link diagrams
