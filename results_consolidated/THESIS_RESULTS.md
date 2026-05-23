# Kintsugi — Consolidated Thesis Results

**One-file reference for thesis writing.** Every number in this document is sourced from a specific file on disk and the source path is listed under each table so it can be re-verified. Where notebook markdown contradicted the actual computed values, the on-disk JSON/CSV is the authority.

---

## 0. Setup and ground truth

- **Domain:** CS1 (introductory Java) knowledge-gap detection on the CodeWorkout dataset.
- **KC vocabulary:** 18 instructor KCs (If/Else, NestedIf, While, For, NestedFor, Math+-*/, Math%, LogicAndNotOr, LogicCompareNum, LogicBoolean, StringFormat, StringConcat, StringIndex, StringLen, StringEqual, CharEqual, ArrayIndex, DefFunction).
- **LLM:** Gemini 2.5 Flash, temperature 0.3 (Gemini 2.0 Flash was used only for the Phase 4 Q-matrix refinement work).
- **Prompt arc:** V1 (curriculum-aware, no scaffolding) → V2 (difficulty-weighted curriculum-aware) → **V3 (CCPP — process-driven prompting, headline claim)**.
- **Final eval cohort:** 10 struggling students (IDs `10155, 9948, 14189, 14352, 14363, 14362, 14374, 14414, 14474, 14499`), 2 human raters (Pranay, Arundhati), **372 common annotations** across the 10 students.
- **Source for cohort + n:** `results/human_validation/all_prompts_eval_results/all_prompts_eval_summary.json` (`n_common_items = 372`, `student_ids = [...10...]`).

---

## 1. Headline result — Final 4-way (5-way with V3) prompt evaluation

**This is the thesis headline.** All five LLM prompt variants evaluated on the same 10 struggling students against the same 2 human raters, with the human-human agreement reported as a ceiling.

| Variant | Problem F1 (avg vs humans) | Jaccard | Cohen κ | Gwet AC1 |
|---|---|---|---|---|
| **Human ceiling (HA vs HB)** | **0.885** | **0.851** | **0.669** | **0.963** |
| **V3 (CCPP)** | **0.839** | **0.806** | **0.557** | **0.953** |
| V2 Baseline | 0.758 | 0.722 | 0.397 | 0.938 |
| V2 Enriched | 0.749 | 0.714 | 0.397 | 0.937 |
| V1 Enriched | 0.730 | 0.689 | 0.382 | 0.930 |
| V1 Baseline | 0.732 | 0.692 | 0.358 | 0.926 |

**V3 as % of human ceiling:**

| Metric | Ceiling | V3 | % of ceiling | Gap |
|---|---|---|---|---|
| Problem F1 | 0.885 | 0.839 | **94.8%** | 0.046 |
| Jaccard | 0.851 | 0.806 | **94.7%** | 0.045 |
| Cohen κ | 0.669 | 0.557 | **83.2%** | 0.112 |
| Gwet AC1 | 0.963 | 0.953 | **98.9%** | 0.010 |

**Ranking by mean % of ceiling** (across all 4 metrics):
1. **V3 (CCPP) — 92.9%**
2. V2 Baseline — 81.8%
3. V2 Enriched — 81.3%
4. V1 Enriched — 79.3%
5. V1 Baseline — 78.4%

**V3 vs Human A vs Human B (separately):**
| Comparison | κ | AC1 (95% CI) | F1 | Jaccard |
|---|---|---|---|---|
| HA vs HB (ceiling) | 0.669 | 0.963 (0.958–0.968) | 0.885 | 0.851 |
| HA vs V3 | 0.578 | 0.954 (0.949–0.960) | 0.850 | 0.817 |
| HB vs V3 | 0.536 | 0.952 (0.946–0.958) | 0.828 | 0.795 |

**Per-student V3 performance** (selected — see source for all 10):
- 5 of 10 students: V3 reaches ≥ 80% of ceiling F1.
- Student 14374: V3 **exceeds** the human ceiling (124% on κ — humans agreed poorly on this student).
- Student 9948 (the hardest): V3 reaches only 48% of ceiling F1, 46% of ceiling κ.

**Methodology note:** "Both-empty" cases (neither rater flagged a gap on a problem) count as F1 = 1.0 and Jaccard = 1.0. Cohen κ is unaffected by this convention. The high AC1 vs lower κ across all variants reflects the prevalence-corrected vs prevalence-sensitive nature of these two metrics — the high "both no-gap" rate inflates AC1.

**Source files (all under `results/human_validation/`):**
- `all_prompts_eval_results/all_prompts_eval_summary.json` — full headline JSON
- `all_prompts_eval_results/all_prompts_headline.csv` — headline + % ceiling per variant
- `all_prompts_eval_results/all_prompts_ranking.csv` — ranking table
- `all_prompts_eval_results/all_prompts_summary.csv` — gap-to-ceiling per metric
- `v3_prompt_eval_results/per_student_metrics.csv` — per-student V3 breakdown
- `v3_prompt_eval_results/overall_metrics.csv` — V3 vs HA, V3 vs HB, ceiling
- `v3_prompt_eval_results/per_kc_pair_metrics.csv` — per-KC, per rater-pair
- `v3_prompt_eval_results/problem_level_metrics.csv` — per-problem stats

---

## 2. Chronological narrative — experiment by experiment

### Phase 1 — Prompt selection

#### Exp 1 — Prompt strategy comparison (2026-03-02)
- **Notebook:** `experiments/phase1_prompt_selection/exp1_prompt_strategy_comparison.ipynb`
- **Question:** Which of 4 prompt strategies (Zero-Shot, Few-Shot, Chain-of-Thought, Curriculum-Aware) to carry forward?
- **Method:** 1 student (ID 14355, avg score 0.17, 5 submissions). Metrics: JSON-validity coverage and average latency only.
- **Result:** All 4 strategies returned valid JSON 5/5 times (100% coverage). Latency: Few-Shot 8.4s · Zero-Shot 10.7s · CoT 12.8s · Curriculum-Aware 14.7s.
- **Status:** ⚠ **No quality measurement was done.** Curriculum-Aware was carried forward as the baseline based on structure alone. This is a methodological gap if asked about.
- **Source:** `results/01_prompt_strategy_comparison/single_student_14355_exp{3,4}*.csv`

---

### Phase 2 — Mental model (V1, simple averaging)

#### Exp 2 — Mental-model POC (2026-03-02)
- **Notebook:** `exp2_mental_model_proof_of_concept.ipynb`
- 1 student (14374), 6 problems, no baseline comparison. Plumbing demo only; final summary cell errored.

#### Exp 3a/b/c — Controlled A/B per cluster (2026-03-02)
- **Notebooks:** `exp3a_controlled_ab_average.ipynb`, `exp3b_controlled_ab_struggling.ipynb`, `exp3c_controlled_ab_high_performer.ipynb`
- **Method:** A = baseline curriculum-aware, B = baseline + mental-model JSON. 1 medoid student per cluster, 12 problems. Metric = WeakOverlap F1 on failing problems.

| Cluster | Student | Weak skills | Baseline F1 | Enriched F1 | Δ |
|---|---|---|---|---|---|
| Average | 14359 | 2 | 0.057 | 0.251 | **+0.194** |
| Struggling | 10155 | 14 | 0.422 | 0.465 | +0.043 |
| High-performer | 14475 | 0 | 0.000 | 0.000 | 0.000 |

- exp3a save cell crashed (NameError) — data is in-notebook only.
- **High-performer result is structurally important:** WeakOverlap F1 is **undefined when the student has no weak skills**. This is a metric limitation, not a prompt failure.
- **Source:** `results/05_mental_model_comparison/v1_simple_average/mental_model_comparison_student_{10155,14359,14475}.csv`

#### Exp 4 — Batch of 28 students (V1 headline) (2026-03-23)
- **Notebook:** `exp4_batch_28_students.ipynb`
- **Method:** 28 students (intended 30; Struggling cluster only had 8 eligible). KMeans(k=3) on 18-skill mastery vectors. 12 problems × 28 students × 2 conditions = 330 evaluable rows × 2.

| | Baseline F1 | Enriched F1 | Δ |
|---|---|---|---|
| Overall | 0.153 | 0.199 | +0.045 |
| Struggling | 0.254 | 0.297 | +0.043 |
| Average | 0.066 | 0.128 | +0.061 |
| High Performer | 0.000 | 0.000 | 0.000 |

- Per-student: 11 improved, 16 unchanged (mostly high performers), 1 worse.
- **Relevance F1 dropped slightly:** 0.611 → 0.580. Enrichment trades precision for recall.
- **Source:** `results/06_batch_30students/{batch_comparison_30students.csv, per_student_summary.csv}`

#### Exp 4b — Corrected F1 metric (2026-03-23)
- **Notebook:** `exp4b_corrected_f1_metric.ipynb` (no cell outputs saved; CSVs exist on disk).
- **Method:** Re-reads exp4 CSV (no new LLM calls). Recomputes F1 on `testable_weak = student_weak ∩ problem_required` only.

| | Corrected Baseline F1 | Corrected Enriched F1 | Δ |
|---|---|---|---|
| Overall (n=58 testable rows out of 330) | 0.332 | 0.372 | **+0.040** |
| Struggling (n=49) | — | — | +0.034 |
| Average (n=9) | — | — | +0.075 |

- **Win rate:** 9/13 students with any weak skill.
- **Take-away:** the original exp4 metric was inflated by counting non-testable skills in the denominator. The corrected effect is real but modest (~+0.04 F1). 82% of rows have no testable weak skill — a structural limitation of the framing.
- **Source:** `results/06_batch_30students/{batch_comparison_30students_corrected.csv, per_student_summary_corrected.csv}`

---

### Phase 3 — Construct validation

#### Exp 5 — Grade correlation + random baseline (2026-03-19)
- **Notebook:** `exp5_grade_correlation_and_baseline.ipynb`
- Three sub-analyses on 3 representative students (10155 struggling, 14359 average, 14475 high-perf):
  - **5A:** Pearson of weak-skill count vs X-Grade across all 372 students. **Significant (p < 0.05).** Construct validity for the mental model.
  - **5B:** Baseline vs Enriched Relevance F1 on 17 failing problems → **0.567 vs 0.570 (Δ = +0.002, essentially flat).**
  - **5C:** 1000 random KC samples per problem. Enriched vs random mean: **+0.052** (struggling, above 95th pct), **+0.101** (average, near 95th pct), 0 (high-perf). Baseline alone is at/below random.
- **Source:** `results/07_validation_analysis/{grade_correlation_data.csv, random_baseline_results.csv, metadata.json}`

#### Exp 6 — Consistency test (2026-03-19)
- **Notebook:** `exp6_consistency_test.ipynb`
- **Method:** Student 14359, 5 failing problems, 3 runs each, Gemini 2.5 Flash @ T=0.3. Pairwise Jaccard between run tag sets.
- **Result:**
  - Overall Jaccard = **0.614 (MODERATE)**. All 10 cases land MODERATE — no HIGH, no LOW.
  - Baseline Jaccard = **0.650**; Enriched Jaccard = **0.577** — enrichment is **slightly less stable**.
  - Core tags (in all 3 runs): avg 2.6. Variable tags: 2.6 (Baseline), 3.8 (Enriched).
- **Caveat for thesis:** single-run results are not highly stable. All downstream V3 numbers (including the 0.557 κ headline) are single-run.
- **Source:** `results/08_consistency_test/consistency_results.csv`

---

### Phase 4 — Knowledge tracing ⚠ exploratory · candidate for cut

Three consecutive negative results for LLM-driven Q-matrix refinement.

#### Exp 7 — PFA baseline comparison (2026-03-29)
- **Notebook:** `exp7_pfa_baseline_comparison.ipynb`
- **Method:** PFA logistic regression, 16,179 first-attempt rows (413 students, 50 problems), 5-fold student-stratified CV.

| Mapping | AUC | vs Instructor |
|---|---|---|
| **Instructor (18 KCs)** | **0.7737 ± 0.0065** | — |
| Enhanced/unconstrained-refined (17 KCs) | 0.7658 ± 0.0079 | Δ −0.0079, p=0.078 (ns) |
| KCGen-KT LLM (11 KCs) | 0.7573 ± 0.0075 | Δ −0.0164, **p=0.0011** |

- **Instructor wins.**
- **Source:** `results/09_pfa_comparison/09_pfa_results.csv`

#### Exp 8a/b/c — Q-matrix refinement (2026-04-02)
- **Notebooks:** `exp8a_qmatrix_unconstrained.ipynb`, `exp8b_qmatrix_additive.ipynb`, `exp8c_pfa_additive_comparison.ipynb`
- **8a (unconstrained):** Gemini 2.0 Flash shown 5 pass + 5 fail per problem, may add/remove KCs. Heavy pruning: 5.2 → 4.0 avg KCs/problem; 68 removals vs 1 addition; NestedIf entirely eliminated (10 → 0). PFA AUC = 0.766 — worse than instructor 0.774.
- **8b (additive-only):** Constrained to only add. 5.2 → 5.8 avg KCs/problem; 36 additions, 0 removals. Problem 31 errored. PFA AUC = 0.7703 ± 0.0120 vs Instructor 0.7737 ± 0.0065 (Δ = −0.0034, paired t p = 0.698, ns).
- **8c (clean 3-way PFA):**

| Mapping | AUC | vs Instructor |
|---|---|---|
| **Instructor** | **0.7737 ± 0.0065** | — |
| Additive (LLM) | 0.7703 ± 0.0120 | Δ −0.0034, p=0.698 (ns) |
| KCGen-KT | 0.7573 ± 0.0075 | Δ −0.0164, p=0.001 |

- **Bottom line:** instructor Q-matrix is the strongest of the three; LLM refinement (either subtractive or additive) does not improve PFA prediction. Many added KCs end up with near-zero learned weights (e.g. LogicBoolean γ = 0.08).
- **Source:** `results/10_qmatrix_refinement/*.csv,*.json` + `results/09_pfa_comparison/12_pfa_additive_results.csv`

---

### Phase 5 — Human validation (the core thesis chapter)

#### Exp 9 — Inter-rater agreement, 1 student (2026-03-29)
- **Notebook:** `exp9_inter_rater_agreement.ipynb`
- 1 student (10155), n=46 common problems.
- **Human–Human κ ≈ 0.559** (substantial agreement, but on 1 student — superseded by the 3-student and 10-student numbers below).
- Pranay vs LLM κ ≈ 0.529; vs majority consensus: Pranay κ=0.854, Arundhati κ=0.817, **LLM κ=0.631** (LLM is the outlier).
- **Source:** `results/human_validation/human_validation_results.json`

#### Exp 10 — V1 baseline + enriched vs human, 3 students (2026-04-03 / 04-10)
- **Notebooks:** `exp10a_baseline_vs_human.ipynb`, `exp10b_enriched_vs_human.ipynb`
- 3 students (10155, 14475, 14476), n = 146 common problems (no empty-problem filter).

| Comparison | Cohen κ | F1 | Precision | Recall |
|---|---|---|---|---|
| Human A vs Human B (ceiling) | 0.421 | 0.459 | 0.398 | 0.543 |
| V1 Baseline avg vs humans | 0.300 | 0.352 | — | — |
| V1 Enriched avg vs humans | 0.321 | 0.359 | — | — |

Per-rater splits:
- V1 Baseline: HA κ=0.383, F1=0.425 · HB κ=0.217, F1=0.280
- V1 Enriched: HA κ=0.417, F1=0.448 · HB κ=0.225, F1=0.271

- **Mental model gives only marginal lift** on V1 (~+0.02 κ).
- Arundhati (HB) systematically tags more KCs → lower agreement with the LLM regardless of variant.
- exp10b adds KC-level disagreement: highest on If/Else (28.8%), LogicCompareNum (26.7%), LogicAndNotOr (25.3%). V1-enriched reaches **76.3% of human baseline**.
- **Source:** `results/human_validation/exp10_baseline_vs_human_metrics.json`, `results/human_validation/human_validation_results_9files.json`

#### Exp 11 — V2 baseline + enriched vs human, 3 students (2026-04-10)
- **Notebooks:** `exp11_baseline_vs_human.ipynb`, `exp11_enriched_vs_human.ipynb`
- Same 3 students, n = 146.

| Comparison | Cohen κ | F1 | Precision | Recall |
|---|---|---|---|---|
| Human A vs Human B (ceiling) | 0.421 | 0.459 | — | — |
| **V2 Baseline avg vs humans** | **0.371** | **0.412** | — | — |
| V2 Enriched avg vs humans | 0.354 | 0.396 | — | — |

Per-rater splits:
- V2 Baseline: HA κ=0.470, F1=0.502 · HB κ=0.273, F1=0.322
- V2 Enriched: HA κ=0.449, F1=0.483 · HB κ=0.258, F1=0.310

- **V2 beats V1** on every variant.
- **V2 Baseline > V2 Enriched** on the 3-student pilot — mental model adds noise rather than signal at V2. **But this result does NOT replicate on the 10-student cohort** (see §1 — V2 Baseline κ=0.397, V2 Enriched κ=0.397 — essentially tied).
- **Source:** `results/human_validation/exp11_baseline_v2_vs_human_metrics.json`, `results/human_validation/exp11_enriched_v2_vs_human_metrics.json`

#### Exp 12 — V3 (CCPP) vs human, 3 students (2026-04-24)
- **Notebook:** `exp12_v3_prompt_experiment.ipynb`
- **Method:** V3 per-problem prompt, skip perfect-score / trivial submissions. Comparison done on **non-empty problems only (n = 44)**, not the n = 146 used in exp10/exp11.

| Comparison | Cohen κ | F1 | Precision | Recall |
|---|---|---|---|---|
| Human A vs Human B (n=44) | **0.513** | 0.596 | 0.661 | 0.543 |
| HA vs V3 | 0.508 | 0.588 | 0.694 | 0.510 |
| HB vs V3 | 0.386 | 0.477 | 0.505 | 0.452 |
| **V3 avg vs humans** | **0.447** | **0.532** | — | — |

- **Bottom line on the pilot:** V3 reaches near-human-pair agreement against Human A (κ 0.508 vs ceiling 0.513).
- **⚠ Caveat for thesis:** the V3 vs V1/V2 table in this notebook mixes denominators (V3 on n=44 filtered; V1/V2 numbers reused from exp10/11 on n=146 unfiltered). The clean apples-to-apples comparison is the 10-student final eval (§1).
- Per-KC V3 κ best on **CharEqual (0.836)**, Math% (0.734), StringConcat (0.658); weakest on If/Else (0.088), LogicCompareNum (0.108), NestedIf (0). Several KCs return NaN (While, NestedFor) — no positive cases in n=44.
- **Source:** `results/human_validation/exp12_v3_vs_human_metrics.json` (also `exp14_v3_vs_human_metrics.json` — supplementary V3 metrics, slightly different per-rater numbers: HA κ=0.460, HB κ=0.388, avg κ=0.424. Use exp12 unless you can identify the exp14 input difference.)

#### Exp 15 — Learning curve validation, 3 students (2026-04-24)
- **Notebook:** `exp15_learning_curve_validation.ipynb` · ⚠ exploratory pilot
- For each problem with a V3 gap tag, find the next temporally-ordered problem requiring that KC. TP if future score < 1.0, FP otherwise.
- **97 validatable predictions, 76 TP / 21 FP = 78.4% hit rate vs 51.2% random.**
- Per-student: 84.2% / 82.7% / 14.3% (last student had only 7 cases). Signal carried by 2 of 3 students.
- **Source:** `results/learning_curve/exp15_learning_curve_summary.json`

#### Exp 16 — Learning curve, 28 students (2026-04-27)
- **Notebook:** `exp16_learning_curve_30students.ipynb` · ⚠ exploratory
- Same method as exp15; 28 students (10 Avg, 10 HP, 8 Struggling). ~250 V3 API calls.
- **226 validatable predictions, 132 TP / 94 FP = 58.4% hit rate vs 26.4% ± 2.8% random** (beats random by > 3σ).

| Cluster | Hit rate | n |
|---|---|---|
| **Struggling** | **77.0%** | 148 |
| Average | 26.5% | 68 |
| High Performer | 0.0% | 10 |

- **⚠ The 58.4% aggregate is misleading on its own** — it's almost entirely from the struggling cluster. High Performer predictions are essentially all false positives. Report with cluster split.
- **Source:** `results/learning_curve/exp16_learning_curve_30students.json`, `exp16_per_student_summary_30students.csv`, `exp16_predictions_30students.csv`

#### Exp 17 — Jaccard similarity across rater pairs, 3 students (2026-04-28)
- **Notebook:** `exp17_jaccard_similarity_analysis.ipynb`
- 3 students, 146 common problems. Filtered to problems where at least one side flagged a gap (n = 14–20 per pair).

| Pair | Mean Jaccard | Mean F1 |
|---|---|---|
| **Human A vs Human B** | **0.543** | 0.663 |
| V1 Enriched vs V2 Enriched | 0.518 | — |
| **Human A vs V3** | **0.512** | 0.621 |
| Human B vs V3 | 0.489 | — |
| V1 Enriched vs V3 | 0.414 | — |
| V2 Enriched vs V3 | 0.394 | — |
| Human vs V2 Enriched | 0.335 / 0.280 | — |
| Human vs V1 Enriched | 0.328 / 0.312 | — |

- **V3 is closer to humans than V1 or V2 are.** Human A vs V3 (0.512) nearly matches Human A vs Human B (0.543) — V3 is within human-rater noise on this pilot.
- **Note:** 3 students only. The 10-student final eval Jaccard is **0.806** (V3) vs **0.851** (ceiling) — see §1.
- **Source:** `results/human_validation/exp17_visualizations/` (figures only; numbers from notebook outputs)

#### Exp 18 — Per-KC power-law curves (2026-05-05)
- **Notebook:** `exp18_kc_learning_curves.ipynb` · ⚠ exploratory · half-executed
- Fits constrained power-law `a · x^b` per-student (442 fits) and aggregate (18 fits).
- **Fits are degenerate:** `b ≈ 0` everywhere (e.g., 10155 If/Else baseline `b = -3.5e-12`). No learning trajectory recovered.
- Notebook executed only through cell 5/8.
- **Source:** `results/human_validation/exp18_*.csv,*.json`

#### Exp 19 — V3 annotation on the 10-struggling cohort (2026-05-05)
- **Notebook:** `exp19_llm_v3_annotation.ipynb`
- V3 prompt (no mental model), per-submission API calls, skip perfect scores. 10 students.
- **188 API calls, 126 problems with gaps flagged, 0 errors.**
- Per-student gap counts: 12, 9, 15, 14, 7, 10, 22, 15, 12, 10.
- **Source:** `results/human_validation/llm_v3_10students/llm_v3_annotations_<sid>.json` (10 files)

#### Exp 20 — V1 + V2 (baseline + enriched) on the 10-student cohort (2026-05-21)
- **Notebook:** `exp20_v1_v2_annotation.ipynb`
- Parametrized notebook with `PROMPT_VARIANT` toggle. Same per-problem API pattern as exp19. Mental model via `lib/mental_model.py` for enriched variants. KC tags extracted from `student_analysis[].knowledge_gaps[].missing_concept` only (matches human semantics).
- All 4 variant directories verified on disk (10 students × 4 variants = 40 files).
- v2_enriched (last saved run): **188 calls, 149 problems with gaps, 0 errors.**
- **Source:** `results/human_validation/llm_v{1,2}_{baseline,enriched}_10students/`

#### Final 4-way evaluation
- See §1 above for the headline numbers.

---

## 3. Cross-cutting findings worth foregrounding in the thesis

1. **V3 (CCPP) is the headline win.** On the 10-student final eval cohort, V3 reaches **94.8% of human ceiling F1 and 83.2% of human ceiling Cohen κ** — and **98.9% of Gwet AC1**. The gap from V2 (the next-best) to V3 is much larger than the gap from V1 to V2.

2. **Mental model has an inconsistent effect.**
   - V1 (3 students): +0.02 κ from enrichment (helps).
   - V2 (3 students): −0.017 κ from enrichment (hurts).
   - V1 (10 students final): +0.024 κ from enrichment (helps slightly).
   - V2 (10 students final): essentially 0 (V2 Baseline κ=0.3974, V2 Enriched κ=0.3974 — tied).
   - V3 does **not** use mental model and beats every enriched variant. **Take-away:** the gains from V3's process-driven scaffolding dominate any gain from the mental model.

3. **Human-rater agreement varies by cohort and filter:**
   - 1 student, n=46: H-H κ = 0.559
   - 3 students, n=146 (unfiltered): H-H κ = 0.421
   - 3 students, n=44 (non-empty filter): H-H κ = 0.513
   - 3 students, n=87 (non-empty filter, cross-comparison notebook): H-H κ = 0.392
   - **10 students final (n=372): H-H κ = 0.669** (this is the ceiling used in the thesis headline)

4. **Phase 4 (KT) is three consecutive negatives.** Instructor Q-matrix beats every LLM-refined alternative on PFA AUC. Either cut from the thesis or frame as a methodological null finding (LLM-refined KCs do not carry PFA-predictive signal).

5. **Predictive validity (exp16) holds only for struggling students.** 77.0% hit rate on struggling, 26.5% on average, 0% on high-performers. Cite with the cluster split.

6. **Single-run LLM stability is moderate** (exp6: Jaccard 0.614). All V3 numbers are single-run. This is a known caveat — recommend reporting core tags + noting variability.

7. **WeakOverlap F1 (Phase 2 metric) is undefined for high-performers** (no weak skills → no denominator). This is why Phase 2 results show 0/0/0 for High Performer everywhere. It is a metric limitation, not a prompt failure.

---

## 4. Known issues / things to fix or footnote

- **exp1** never measured prompt quality. Curriculum-Aware was adopted on structure (JSON validity + latency) alone.
- **exp4b** notebook has no cell outputs — CSVs were written but the notebook needs a rerun to embed figures.
- **exp12** V3 vs V1/V2 comparison table inside the notebook mixes denominators (n=44 vs n=146). Cite §1 for the apples-to-apples comparison instead.
- **exp14** metrics JSON gives slightly different V3 vs HA/HB numbers than exp12. Source of the divergence is unclear — likely a different input file. Default to exp12 unless you can verify exp14's input.
- **exp17** is on 3 students; the 10-student Jaccard headline is in §1.
- **exp18** power-law fits are degenerate (`b ≈ 0`); cells 6–9 unexecuted. Cut or rebuild.
- **exp9** "76.3% of human baseline" claim comes from exp10b — verify your phrasing if citing.
- **n=372 final cohort note:** this is the count of common annotations across all 6 raters (HA, HB, V1B, V1E, V2B, V2E, V3) — i.e., the intersection of problems where every rater (or "no-gap" from every rater) is present.

---

## 5. File map (where to look)

All paths relative to project root.

```
Final headline numbers       →  results/human_validation/all_prompts_eval_results/
                                results/human_validation/v3_prompt_eval_results/
V3 annotations (10 students) →  results/human_validation/llm_v3_10students/
V1/V2 annotations (10 stu.)  →  results/human_validation/llm_v{1,2}_{baseline,enriched}_10students/

Pilot (3 students) metrics   →  results/human_validation/exp{10,11,12,14}_*_vs_human_metrics.json
Pilot annotation files       →  results/human_validation/llm_*_annotations_*.json

Phase 2 mental model         →  results/05_mental_model_comparison/v1_simple_average/
Phase 2 batch (28 students)  →  results/06_batch_30students/

Phase 3 validation           →  results/07_validation_analysis/  (grade correlation, random baseline)
                                results/08_consistency_test/      (Jaccard across reruns)

Phase 4 PFA                  →  results/09_pfa_comparison/        (exp7, exp8c)
Phase 4 Q-matrix             →  results/10_qmatrix_refinement/    (exp8a, exp8b)

Learning curves              →  results/learning_curve/           (exp15, exp16)
Per-KC learning curves       →  results/human_validation/exp18_*

Visualizations               →  results/human_validation/exp{12,17,18,19}_visualizations/
                                results/learning_curve/exp16_visualizations/
                                results/visualizations/

Notebooks                    →  experiments/phase{1,2,3,4,5}_*/
Prompts library              →  lib/prompts/        (V1, V2, V3 = build_v3_prompt)
Mental model builder         →  lib/mental_model.py
```

A copy of every result file in this index also lives under `results_consolidated/phase{1-5}_*/exp*/` with per-experiment READMEs. Use either — content is the same.
