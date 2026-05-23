# Exp 6 — LLM Output Consistency Test

- **Date:** 2026-03-19
- **Phase:** 3 (Construct validation)
- **Notebook:** [exp6_consistency_test.ipynb](../../../experiments/phase3_validation/exp6_consistency_test.ipynb)
- **Status:** ✓ Important limitation finding. Caveat applies to all single-run V3 claims downstream.

## Question
Are single-run LLM KC tag outputs stable enough to trust, or do we need majority voting?

## Method
- Student 14359, 5 failing problems
- NUM_RUNS = 3 per problem
- Gemini 2.5 Flash, temperature = 0.3
- Both Baseline and Enriched (curriculum-aware) prompts
- Metric: pairwise Jaccard similarity between run tag sets

## Key result
- **Overall Jaccard = 0.614 (MODERATE).** All 10 cases land in the MODERATE band — no HIGH, no LOW.
- Baseline Jaccard = 0.650; Enriched Jaccard = 0.577 — enrichment is **slightly less stable** across reruns.
- Core tags (present in all 3 runs): avg 2.6. Variable tags: 2.6 (Baseline), 3.8 (Enriched).
- **Recommendation:** report core tags + note variability; single-run results are not highly stable.

## Files
- `consistency_results.csv` — per-problem, per-condition Jaccard and tag breakdowns
- `metadata.json` — run config
