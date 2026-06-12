# V3 (KCDP) Prompt Ablation Results

Scored against the 2-rater human gold standard over 372 common problem annotations (10 struggling students). Metrics are the AvgHuman-vs-LLM row from `utils.metrics.evaluate_llm_vs_humans` (the same scorer behind the V3 headline numbers). Model: gemini-2.5-flash, temperature 0.3. Only the prompt varies between conditions.

Parse % = fraction of LLM-called problems with a valid `parsed_response` (perfect-score problems are skipped, not called).

| Condition | KC injection | Rules | F1 | κ | AC1 | Parse % |
|---|---|---|---|---|---|---|
| baseline | per_problem | full (14) | 0.831 | 0.548 | 0.953 | 96.3% |
| no_rules | per_problem | none (0) | 0.847 | 0.571 | 0.952 | 98.9% |
| reduced | per_problem | reduced (4) | 0.829 | 0.533 | 0.949 | 96.3% |
| no_kc | full_vocab | full (14) | 0.820 | 0.496 | 0.950 | 98.4% |
