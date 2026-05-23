# Exp 5 — Grade Correlation, Relevance F1, Random Baseline

- **Date:** 2026-03-19
- **Phase:** 3 (Construct validation)
- **Notebook:** [exp5_grade_correlation_and_baseline.ipynb](../../../experiments/phase3_validation/exp5_grade_correlation_and_baseline.ipynb)
- **Status:** ✓ Healthy validation. Grade correlation is the strongest signal. Likely superseded by Phase 5 human-rater eval for the headline thesis claim, but useful as construct validity.

## Question
1. Does the mental model (weak-skill count) track real student ability?
2. Does the LLM beat a random tagging baseline on weak-skill overlap?

## Method
Three sub-analyses on the 3 representative students (10155 struggling, 14359 average, 14475 high-perf):
- **5A — Grade correlation:** Pearson of weak-skill count vs X-Grade across all 372 students.
- **5B — Relevance F1:** Baseline vs Enriched on 17 failing problems.
- **5C — Random baseline:** 1000 random KC samples per problem vs actual Enriched.

## Key result
- **5A:** Weak-skill count ↔ grade significant (p < 0.05); AvgScore ↔ Grade strong. Provides construct validity for the mental model.
- **5B:** Overall Baseline Rel F1 = 0.567, Enriched = 0.570 (Δ = +0.002). **Essentially flat** — enrichment doesn't help relevance.
- **5C:** Enriched vs random mean: +0.052 (struggling, above 95th pct), +0.101 (average, near 95th pct), 0 (high-perf). Baseline alone is at/below random.

## Files
- `grade_correlation_data.csv` — per-student weak-skill counts and grades
- `grade_correlation_plots.png` — correlation scatterplots
- `random_baseline_results.csv` — random-sampling distribution per problem
- `metadata.json` — run config
