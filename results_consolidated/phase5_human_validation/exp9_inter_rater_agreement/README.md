# Exp 9 — Human Inter-Rater Agreement (single student)

- **Date:** 2026-03-29
- **Phase:** 5 (Human validation) · pilot
- **Notebook:** [exp9_inter_rater_agreement.ipynb](../../../experiments/phase5_human_validation/exp9_inter_rater_agreement.ipynb)
- **Status:** Superseded by the 3-student inter-rater numbers in exp10/exp11. Useful as a sanity check only — n=46 is too small to be a headline IRR figure.

## Question
How well do the two human raters agree, and how does the V1 (enriched) LLM compare?

## Method
- 1 student only (10155), n=46 common problems
- Raters: Pranay, Arundhati, LLM (V1 enriched, `llm_annotations_10155.json`)
- Computes pairwise Cohen's κ, F1, per-KC κ, and a 2-of-3 majority-vote consensus

## Key result
- Human–Human κ ≈ **0.559** (substantial agreement on this single student)
- Pranay vs LLM κ ≈ 0.529
- Arundhati vs LLM κ lower
- Vs majority consensus: Pranay κ=0.854 · Arundhati κ=0.817 · **LLM κ=0.631** (LLM is the outlier)

## Files
- `human_validation_results.json` — raw saved comparison
