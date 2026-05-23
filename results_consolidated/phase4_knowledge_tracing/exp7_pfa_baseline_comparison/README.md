# Exp 7 — PFA Baseline Comparison (KCGen-KT vs Instructor vs Enhanced)

- **Date:** 2026-03-29
- **Phase:** 4 (Knowledge tracing) · ⚠ exploratory — may be cut from thesis
- **Notebook:** [exp7_pfa_baseline_comparison.ipynb](../../../experiments/phase4_knowledge_tracing/exp7_pfa_baseline_comparison.ipynb)
- **Status:** Negative result for the LLM-refinement hypothesis. Instructor Q-matrix wins.

## Question
Which KC mapping yields better PFA prediction of first-attempt correctness — instructor, KCGen-KT (LLM), or LLM-refined?

## Method
- PFA logistic regression on 16,179 first-attempt rows (413 students, 50 problems)
- 5-fold student-stratified cross-validation
- Three KC maps compared:
  - **KCGen-KT** LLM mapping (11 KCs)
  - **Instructor** mapping (18 KCs)
  - **Enhanced** loaded from `run3_kc_mapping.json` — at this point the exp8a *unconstrained* refined map (17 KCs)

## Key result
| Mapping | AUC | vs Instructor |
|---|---|---|
| Instructor | **0.7737 ± 0.0065** | — |
| Enhanced (unconstrained) | 0.7658 ± 0.0079 | Δ −0.0079, p=0.078 (ns) |
| KCGen-KT | 0.7573 ± 0.0075 | Δ −0.0164, **p=0.0011** |

- **Instructor wins.** LLM-refined (unconstrained) is statistically indistinguishable but slightly worse.
- KCGen-KT vs Instructor difference is significant.

## Files
- `09_pfa_results.csv` — per-fold AUC and parameter estimates
