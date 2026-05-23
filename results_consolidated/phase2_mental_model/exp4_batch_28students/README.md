# Exp 4 — Batch of 28 Students (V1 mental-model headline)

- **Date:** 2026-03-23
- **Phase:** 2 (Mental model) · V1 simple-average headline
- **Notebook:** [exp4_batch_28_students.ipynb](../../../experiments/phase2_mental_model/exp4_batch_28_students.ipynb)
- **Status:** ⚠ Headline F1 metric was later flagged as inflated. See [exp4b](../exp4b_corrected_f1/README.md) for the correction.

## Question
Does mental-model enrichment improve weak-skill overlap F1 at scale, across the three student clusters?

## Method
- 28 students (target was 30; Struggling cluster only had 8 eligible)
- KMeans(k=3) on 18-skill mastery vectors → Struggling / Average / High Performer
- 12 problems × 28 students × 2 conditions = 330 evaluable rows × 2
- Metric: WeakOverlap F1 (later corrected in exp4b)

## Key result (as originally reported — see exp4b for corrected numbers)
| | Baseline F1 | Enriched F1 | Δ |
|---|---|---|---|
| Overall | 0.153 | 0.199 | +0.045 |
| Struggling | 0.254 | 0.297 | +0.043 |
| Average | 0.066 | 0.128 | +0.061 |
| High Performer | 0.000 | 0.000 | 0.000 |

- Per-student: 11 improved, 16 same (mostly high-performers), 1 worse.
- **Relevance F1 actually decreased slightly** (0.611 → 0.580) — enrichment trades precision for recall.
- Includes 10 hardcoded cases used as the basis for the Phase-3 human-validation set.

## Files
- `batch_comparison_30students.csv` — full per-row results
- `per_student_summary.csv` — aggregated per student
- `checkpoint_*.csv` — incremental saves during the 28-student run
- `metadata.json` — run config
