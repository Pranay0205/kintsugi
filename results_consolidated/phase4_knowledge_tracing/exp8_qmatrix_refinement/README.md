# Exp 8 — Q-Matrix Refinement (Unconstrained + Additive)

- **Date:** 2026-04-02
- **Phase:** 4 (Knowledge tracing) · ⚠ exploratory — may be cut from thesis
- **Notebooks:**
  - [exp8a_qmatrix_unconstrained.ipynb](../../../experiments/phase4_knowledge_tracing/exp8a_qmatrix_unconstrained.ipynb)
  - [exp8b_qmatrix_additive.ipynb](../../../experiments/phase4_knowledge_tracing/exp8b_qmatrix_additive.ipynb)
  - [exp8c_pfa_additive_comparison.ipynb](../../../experiments/phase4_knowledge_tracing/exp8c_pfa_additive_comparison.ipynb)
- **Status:** Three consecutive negative results for LLM-driven KC refinement. Frame as a methodological null if kept.

## Question
Can an LLM, shown passing/failing code samples per problem, refine instructor KC tags to better predict failure (via PFA)?

## Method
- **exp8a (unconstrained):** Gemini 2.0 Flash shown 5 passing + 5 failing attempts per problem, may add or remove KCs. Builds refined Q-matrix.
- **exp8b (additive-only):** Same setup but the prompt constrains the LLM to **only add** KCs (never remove instructor tags).
- **exp8c:** Clean 3-way PFA comparison with the additive Q-matrix.

## Key result
**exp8a (unconstrained):** heavy pruning — avg KCs/problem 5.2 → 4.0; 68 removals vs 1 addition; 39/50 problems changed. NestedIf entirely eliminated (10→0). Result feeds into exp7 — PFA AUC 0.766, *worse* than instructor 0.774.

**exp8b (additive-only):** avg KCs 5.2 → 5.8; 32/49 problems got additions; 36 tags added, 0 removed. Biggest additions: LogicBoolean (+11), LogicAndNotOr (+3). Problem 31 errored.

**exp8c — clean PFA 3-way:**
| Mapping | AUC | vs Instructor |
|---|---|---|
| Instructor | **0.7737 ± 0.0065** | — |
| Additive (LLM) | 0.7703 ± 0.0120 | Δ −0.0034, p=0.698 (ns) |
| KCGen-KT | 0.7573 ± 0.0075 | Δ −0.0164, p=0.001 |

- **Instructor still wins.** Additive refinement is statistically indistinguishable but does not improve PFA.
- Many added KCs end up with near-zero PFA weights (e.g. LogicBoolean γ=0.08) — LLM-suggested KCs do not carry predictive signal.

## Files
- `qmatrix_refinement_results.csv` — exp8a per-problem decisions
- `qmatrix_additive_results.csv` — exp8b per-problem additions
- `refined_problem_prompts.csv` — exp8a prompts
- `additive_problem_prompts.csv` — exp8b prompts
- `run3_kc_mapping.json` — refined KC map consumed by PFA
- `run3_refinement_prompts.json` — full prompt traces
- `12_pfa_additive_results.csv` — exp8c per-fold AUC
