# V3 (KCDP) Ablation — Two Views

AvgHuman view (mean of HA-pred and HB-pred) over 372 common problem annotations (human_a ∩ human_b ∩ baseline LLM run), the same pid list as the main V3 eval. H-H ceiling = HA vs HB under each table's own definitions.

## Table A — FULL-TASK (empties included)

Existing scorer from `utils.metrics`; both-empty problems count as agreement, and κ/AC1 are over all 18 KC slots for every problem. Precision/recall use the same empty-set conventions as `problem_f1` (both-empty = 1.0, exactly-one-empty = 0.0), per-problem mean then averaged across raters.

| cond | Problem_F1 | precision | recall | Jaccard | Cohen_kappa | Gwet_AC1 |
|---|---|---|---|---|---|---|
| baseline | 0.831 | 0.858 | 0.829 | 0.794 | 0.548 | 0.953 |
| no_rules | 0.847 | 0.868 | 0.852 | 0.809 | 0.571 | 0.952 |
| reduced | 0.829 | 0.852 | 0.831 | 0.792 | 0.533 | 0.949 |
| no_kc | 0.820 | 0.859 | 0.809 | 0.782 | 0.496 | 0.950 |
| H-H (ceiling) | 0.885 | 0.906 | 0.881 | 0.851 | 0.669 | 0.963 |

## Table B — GAP-ONLY (empties removed, micro)

Problems where BOTH human and pred are empty are skipped. Over the kept problems: tp/fp/fn summed across problems, then micro precision/recall/F1. exact_match = fraction of kept problems where the gap sets are identical; n = number of kept problems.

| cond | precision | recall | F1 | exact_match | n |
|---|---|---|---|---|---|
| baseline | 0.605 | 0.540 | 0.570 | 0.131 | 133.5 |
| no_rules | 0.585 | 0.603 | 0.594 | 0.164 | 134.0 |
| reduced | 0.569 | 0.546 | 0.557 | 0.113 | 133.0 |
| no_kc | 0.590 | 0.464 | 0.519 | 0.126 | 135.0 |
| H-H (ceiling) | 0.718 | 0.658 | 0.687 | 0.252 | 131.0 |
