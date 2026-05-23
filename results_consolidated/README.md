# Kintsugi — Consolidated Results

A chronological, traceable view of every experiment in the thesis arc. Files in this folder are **copies** — originals remain at their primary locations in `results/`. Each experiment subfolder has its own `README.md` with the question, method, key result, and a list of files.

## Thesis arc

**V1 (simple averaging) → V2 (difficulty weighted) → V3 (CCPP — process-driven prompting, the headline claim) → Final 4-way human-rater evaluation on 10 struggling students.**

Phase 4 (Knowledge Tracing) is included but marked exploratory — may be cut from the final thesis. It is a sequence of negative results for LLM-driven Q-matrix refinement.

## Chronological index

| # | Date | Phase | Experiment | Status | Headline |
|---|---|---|---|---|---|
| 1 | 2026-03-02 | 1 | [Prompt strategy comparison](phase1_prompt_selection/exp1_prompt_strategy_comparison/) | ✓ smoke test | All 4 strategies produce valid JSON; Curriculum-Aware chosen as baseline (no quality measured) |
| 2–3 | 2026-03-02 | 2 | [Mental-model POC + A/B](phase2_mental_model/exp2_3_mental_model_poc_and_ab/) | superseded by exp4 | Enrichment helps for low-weak-skill students; metric undefined for high performers |
| 5 | 2026-03-19 | 3 | [Grade correlation + random baseline](phase3_validation/exp5_grade_correlation_baseline/) | ✓ construct validity | Weak-skill count correlates with grade; enrichment beats random for struggling/avg, not high-perf |
| 6 | 2026-03-19 | 3 | [Consistency test](phase3_validation/exp6_consistency_test/) | ✓ limitation finding | Single-run Jaccard = 0.614 (moderate); enrichment slightly less stable |
| 4 | 2026-03-23 | 2 | [Batch of 28 students (V1)](phase2_mental_model/exp4_batch_28students/) | ⚠ headline F1 inflated | Overall +0.045 F1 from enrichment; relevance F1 actually drops |
| 4b | 2026-03-23 | 2 | [Corrected F1 metric](phase2_mental_model/exp4b_corrected_f1/) | ✓ supersedes exp4 | Corrected Δ = +0.040 F1; only 58/330 rows have any testable weak skill |
| 7 | 2026-03-29 | 4 | [PFA baseline comparison](phase4_knowledge_tracing/exp7_pfa_baseline_comparison/) | ⚠ exploratory · negative | Instructor Q-matrix wins (AUC 0.774); LLM-refined slightly worse |
| 9 | 2026-03-29 | 5 | [Inter-rater agreement (1 student)](phase5_human_validation/exp9_inter_rater_agreement/) | pilot | H-H κ ≈ 0.559 on 1 student; superseded by 3-student exp10 |
| 8a/b/c | 2026-04-02 | 4 | [Q-matrix refinement](phase4_knowledge_tracing/exp8_qmatrix_refinement/) | ⚠ exploratory · negative | Neither unconstrained nor additive LLM refinement beats instructor baseline |
| 10 | 2026-04-03 / 04-10 | 5 | [V1 baseline+enriched vs human (3 students)](phase5_human_validation/exp10_v1_baseline_enriched_vs_human/) | ✓ V1 final (pilot) | V1 Baseline κ=0.300; V1 Enriched κ=0.321; H-H κ=0.421 |
| 11 | 2026-04-10 | 5 | [V2 baseline+enriched vs human (3 students)](phase5_human_validation/exp11_v2_baseline_enriched_vs_human/) | ✓ V2 final (pilot) | **V2 Baseline κ=0.371 > V2 Enriched κ=0.354** — mental model hurts on V2 |
| — | 2026-04-10 | 5 | (V1 vs V2 cross-comparison, no V3) | side analysis | n=87 filtered: V2 Baseline still best of the four V1/V2 variants |
| — | 2026-04-17 | 5 | (visualization_of_metrics) | superseded by exp17 | V2-era heatmaps; not a V3 result |
| 12 | 2026-04-24 | 5 | [V3 (CCPP) vs human (3 students)](phase5_human_validation/exp12_v3_vs_human/) | ⚠ first V3 numbers | **V3 κ=0.447, F1=0.532** on n=44 — beats V1/V2 but denominator differs |
| 15 | 2026-04-24 | 5 | [Learning curve validation (3 students)](phase5_human_validation/exp15_learning_curve_validation/) | ⚠ exploratory pilot | 78.4% hit rate vs 51.2% random (n=97); 2 of 3 students carry the signal |
| 16 | 2026-04-27 | 5 | [Learning curve (28 students)](phase5_human_validation/exp16_learning_curve_30students/) | ⚠ exploratory | **58.4% hit rate vs 26.4% random** — but Struggling 77% / Avg 26.5% / HP 0% |
| 17 | 2026-04-28 | 5 | [Jaccard similarity (3 students)](phase5_human_validation/exp17_jaccard_similarity/) | cleanest agreement story | H-V3 Jaccard 0.512 ≈ H-H 0.543 — V3 within human-rater noise |
| 18 | 2026-05-05 | 5 | [Per-KC power-law curves](phase5_human_validation/exp18_kc_learning_curves/) | ⚠ degenerate fits | Fits ran but `b ≈ 0`; cells 6-9 not executed |
| 19 | 2026-05-05 | 5 | [V3 on 10-student cohort](phase5_human_validation/exp19_v3_on_10students/) | ✓ final eval input | 188 calls, 126 problems with gaps, 0 errors |
| 20 | 2026-05-21 | 5 | [V1+V2 (baseline+enriched) on 10-student cohort](phase5_human_validation/exp20_v1_v2_on_10students/) | ✓ final eval input | All 4 variants generated; enables fair 4-way comparison |
| — | — | 5 | [**Final 4-way prompt evaluation**](phase5_human_validation/final_4way_prompt_evaluation/) | ✓ thesis headline | Consolidated `all_prompts_*` + `v3_eval/*` tables on the 10-struggling cohort |

## Phase summary

- **Phase 1 — Prompt selection** (exp1): smoke test only. Curriculum-Aware chosen without a quality measurement.
- **Phase 2 — Mental model (V1)** (exp2–4b): enrichment effect is real but small (~+0.04 F1) and undefined for high performers. Metric had to be corrected (exp4b).
- **Phase 3 — Construct validation** (exp5–6): weak-skill counts correlate with grades; single-run outputs are only moderately consistent (Jaccard 0.61).
- **Phase 4 — Knowledge tracing** (exp7–8c): ⚠ three consecutive negative results. Instructor Q-matrix beats every LLM-refined alternative. **Candidate for cut.**
- **Phase 5 — Human validation** (exp9–20 + final eval): pilot on 3 students → V3 wins on κ and F1 → re-run on 10-struggling-student cohort with 2 human raters and 372 common annotations gives the **headline 4-way comparison** in `final_4way_prompt_evaluation/`.

## Known caveats / things to fix

- **exp12** V3 vs V1/V2 table mixes denominators (V3 on n=44 vs V1/V2 on n=146). The fair comparison is `final_4way_prompt_evaluation/`.
- **exp4b** notebook has no cell outputs — CSVs exist but a rerun is needed to embed visuals.
- **exp18** power-law fits are degenerate; only run through cell 5/8.
- **exp17** is on 3 students only — needs rerun on the 10-student cohort to be thesis-quotable as a Jaccard headline.
- **exp16** 58.4% headline is misleading without the cluster split — the signal is from struggling students only.

## Conventions
Each experiment folder contains:
- `README.md` — date, phase, notebook link, question, method, key result, file list
- Result artifacts (CSV / JSON / PNG), copied from their primary locations under `results/`
