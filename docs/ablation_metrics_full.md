# V3 (KCDP) Prompt Ablation — Full Metrics

AvgHuman view (mean of HA-LLM and HB-LLM) over 372 common problem annotations (human_a ∩ human_b ∩ baseline LLM run), the same pid list as the main V3 eval. Problem_F1, Jaccard, Cohen_kappa and Gwet_AC1 come from `utils.metrics`; precision/recall use the same empty-set conventions as `problem_f1` (both-empty = 1.0, exactly-one-empty = 0.0), averaged per-problem then across the two raters. mean_tags columns are over-tagging diagnostics on the LLM gap sets only.

| Condition | mean_tags_per_problem | mean_tags_per_gap_prob | Problem_F1 | mean_precision | mean_recall | Jaccard | Cohen_kappa | Gwet_AC1 |
|---|---|---|---|---|---|---|---|---|
| baseline | 0.847 | 2.520 | 0.831 | 0.858 | 0.829 | 0.794 | 0.548 | 0.953 |
| no_rules | 0.976 | 2.771 | 0.847 | 0.868 | 0.852 | 0.809 | 0.571 | 0.952 |
| reduced | 0.911 | 2.734 | 0.829 | 0.852 | 0.831 | 0.792 | 0.533 | 0.949 |
| no_kc | 0.745 | 2.131 | 0.820 | 0.859 | 0.809 | 0.782 | 0.496 | 0.950 |
