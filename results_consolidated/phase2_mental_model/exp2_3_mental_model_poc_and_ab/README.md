# Exp 2 & 3 — Mental-Model POC and Controlled A/B

- **Date:** 2026-03-02
- **Phase:** 2 (Mental model) · V1 simple-average
- **Notebooks:**
  - [exp2_mental_model_proof_of_concept.ipynb](../../../experiments/phase2_mental_model/exp2_mental_model_proof_of_concept.ipynb)
  - [exp3a_controlled_ab_average.ipynb](../../../experiments/phase2_mental_model/exp3a_controlled_ab_average.ipynb)
  - [exp3b_controlled_ab_struggling.ipynb](../../../experiments/phase2_mental_model/exp3b_controlled_ab_struggling.ipynb)
  - [exp3c_controlled_ab_high_performer.ipynb](../../../experiments/phase2_mental_model/exp3c_controlled_ab_high_performer.ipynb)
- **Status:** Superseded by exp4 batch run. Useful as scoped sanity checks.

## Question
Does adding a per-student mental-model payload (weak skills + prereq graph) to the Curriculum-Aware prompt improve weak-skill overlap F1?

## Method
- **exp2:** plumbing demo on 1 student (14374), 6 problems, no baseline comparison. Final summary cell errored.
- **exp3a/b/c:** A (baseline curriculum-aware) vs B (baseline + mental model JSON), 1 medoid student per cluster (average/struggling/high-perf), 12 problems each. Metric = WeakOverlap F1 on failing problems.

## Key result
| Cluster | Student | Weak skills | Baseline F1 | Enriched F1 | Δ |
|---|---|---|---|---|---|
| Average | 14359 | 2 | 0.057 | 0.251 | +0.194 |
| Struggling | 10155 | 14 | 0.422 | 0.465 | +0.043 |
| High-performer | 14475 | 0 | 0.000 | 0.000 | 0.000 |

- exp3a save cell crashed (NameError) — data is in-notebook only.
- High-performer result confirms the metric is **undefined when the student has no weak skills** — this is a structural problem with the F1 metric, not a property of the prompt.

## Files (from `results/05_mental_model_comparison/v1_simple_average/`)
- `mental_model_comparison_student_10155.csv` — exp3b (struggling)
- `mental_model_comparison_student_14359.csv` — exp3a (average)
- `mental_model_comparison_student_14475.csv` — exp3c (high-performer)
- `mental_model_context_enriched_student_14374.csv` — exp2 (POC)
