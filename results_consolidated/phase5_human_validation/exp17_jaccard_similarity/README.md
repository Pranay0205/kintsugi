# Exp 17 — Jaccard Similarity Across Rater Pairs

- **Date:** 2026-04-28
- **Phase:** 5 (Human validation) · pilot agreement analysis (3-student cohort)
- **Notebook:** [exp17_jaccard_similarity_analysis.ipynb](../../../experiments/phase5_human_validation/exp17_jaccard_similarity_analysis.ipynb)
- **Status:** Cleanest agreement result among LLM variants — V3 ≈ Human-Human Jaccard. But on **only 3 students**; needs rerun on the 10-student cohort to be thesis-quotable.

## Question
How similar are per-problem KC-gap sets across all 5 rater pairs (Human A, Human B, V1 Enriched, V2 Enriched, V3)?

## Method
- 3 students, 146 common problems
- Per-problem Precision / Recall / F1 / Jaccard for all 10 rater pairs (sklearn)
- Filtered to problems where at least one side flagged a gap (n = 14–20 per pair)

## Key result (mean Jaccard, ranked)
| Pair | Jaccard | F1 |
|---|---|---|
| **Human A vs Human B** | **0.543** | 0.663 |
| V1 Enriched vs V2 Enriched | 0.518 | — |
| **Human A vs V3** | **0.512** | 0.621 |
| Human B vs V3 | 0.489 | — |
| V1 Enriched vs V3 | 0.414 | — |
| V2 Enriched vs V3 | 0.394 | — |
| Human vs V2 Enriched | 0.335 / 0.280 | — |
| Human vs V1 Enriched | 0.328 / 0.312 | — |

- **V3 is closer to humans than V1 or V2 are.**
- Human A vs V3 (0.512) **nearly matches Human A vs Human B (0.543)** — V3 is within human-rater noise.

## Files
- `exp17_visualizations/` — Jaccard heatmaps and rater-pair plots
