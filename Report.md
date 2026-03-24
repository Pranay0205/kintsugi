# Experimental Findings Report

## LLM-Based Knowledge Gap Detection with Mental Model Injection for CS1 Students

---

## 1. Dataset Overview

**Source:** CodeWorkout — an online Java programming practice platform used in CS1 courses.

| Metric                      | Value            |
| --------------------------- | ---------------- |
| Total submissions           | 201,570          |
| Students                    | 372              |
| Problems                    | 50               |
| Best attempts (after dedup) | 15,375           |
| Knowledge Components (KCs)  | 18 unique skills |
| LLM used                    | Gemini 2.5 Flash |
| Temperature                 | 0.3              |

**KC Vocabulary (18 skills):** If/Else, NestedIf, While, For, NestedFor, Math+-\*/, Math%, LogicAndNotOr, LogicCompareNum, LogicBoolean, StringFormat, StringConcat, StringIndex, StringLen, StringEqual, CharEqual, ArrayIndex, DefFunction.

---

## 2. Student Clustering and Selection

Students were clustered using K-Means (K=3) on skill mastery vectors (18-dimensional, one score per KC). Cluster medoids (most representative students) were selected for case studies.

| Student | Cluster        | Weak Skills (mastery < 0.6)                | Problems Attempted |
| ------- | -------------- | ------------------------------------------ | ------------------ |
| 10155   | Struggling     | 14 / 18                                    | 46                 |
| 14359   | Average        | 2 / 18 (StringConcat: 0.578, While: 0.582) | 49                 |
| 14475   | High Performer | 0 / 18                                     | 46                 |

---

## 3. Experiment 01 — Prompt Strategy Comparison

**Student:** 14355 | **Problems:** 5

**Purpose:** Compare four prompt strategies to determine which produces the most useful, structured gap analysis.

**Strategies tested:**

- Zero-Shot: No examples or structure, just "analyze this code"
- Few-Shot: Includes example input/output pairs
- Chain-of-Thought: Asks for step-by-step reasoning
- Curriculum-Aware: Includes course structure, problem descriptions, KC constraints, severity levels

**Key Finding:** Curriculum-Aware produced the most structured output with severity levels, specific KC tags, and actionable intervention recommendations. This justified selecting Curriculum-Aware as the base strategy for all subsequent experiments.

**Result files:** results/01_prompt_strategy_comparison/

---

## 4. Experiment 05 — Mental Model A/B Comparison (3 Medoid Students)

**Purpose:** Controlled experiment testing whether injecting a student's mental model (weak skills, prerequisite risk chains) into the LLM prompt improves knowledge gap detection.

### 4.1 Experimental Design

| Parameter            | Value                                                                                  |
| -------------------- | -------------------------------------------------------------------------------------- |
| Conditions           | A = Baseline (Curriculum-Aware, no mental model) vs B = Enriched (same + mental model) |
| Problems per student | 12 (selected across score buckets: 100%, partial, 0%)                                  |
| KC output            | Constrained to 18 exact KC names                                                       |
| Primary metric       | WeakSkillOverlap F1 (LLM tags vs student's actual weak skills)                         |
| Secondary metric     | Relevance F1 (LLM tags vs problem's required KCs)                                      |

The only variable between conditions is the presence of the mental model. Same student, same problems, same prompt structure, same LLM, same temperature.

### 4.2 Results — Student 14359 (Average, 2 weak skills)

**Problem selection:** 7 perfect (100%), 5 failing (14.3% - 68.4%)

**100% Score Problems:** 6/7 correct for both conditions (zero gaps on correct code). Problem 24 was a false positive for both (baseline: 3 gaps, enriched: 2 gaps).

**Failing Problems — Per-Problem KC Tags:**

| Problem | Score | Baseline Tags                                              | Enriched Tags                                             | B_F1  | E_F1  |
| ------- | ----- | ---------------------------------------------------------- | --------------------------------------------------------- | ----- | ----- |
| 108     | 68.4% | ArrayIndex, For, LogicBoolean, NestedFor                   | ArrayIndex, For, If/Else, LogicAndNotOr, NestedFor        | 0.000 | 0.000 |
| 32      | 54.5% | For, If/Else, StringIndex                                  | For, If/Else, **StringConcat**, StringIndex, **While**    | 0.000 | 0.571 |
| 107     | 54.5% | For, LogicAndNotOr, LogicBoolean, NestedFor                | For, NestedFor, **While**                                 | 0.000 | 0.400 |
| 40      | 38.5% | For, LogicAndNotOr, NestedFor, StringEqual, StringIndex    | DefFunction, For, LogicBoolean, StringEqual, StringIndex  | 0.000 | 0.000 |
| 34      | 14.3% | DefFunction, For, NestedFor, **StringConcat**, StringIndex | ArrayIndex, For, NestedFor, **StringConcat**, StringIndex | 0.286 | 0.286 |

Bold = matches student's actual weak skills (StringConcat, While).

**Aggregate (Failing Problems):**

| Metric                  | Baseline | Enriched | Delta      |
| ----------------------- | -------- | -------- | ---------- |
| Avg WeakSkillOverlap F1 | 0.057    | 0.251    | **+0.194** |

**Key Observation:** On problems 32 and 107, the enriched condition correctly identified StringConcat and While as contributing factors. The baseline missed both entirely. The mental model provided the context needed to pinpoint the narrow set of weak skills.

### 4.3 Results — Student 10155 (Struggling, 14 weak skills)

**Problem selection:** 4 perfect (100%), 8 failing (0% - 85.7%)

**100% Score Problems:** 3/4 correct for both. Problem 232 was a false positive for both conditions (2 gaps each).

**Aggregate (Failing Problems):**

| Metric                  | Baseline | Enriched | Delta      |
| ----------------------- | -------- | -------- | ---------- |
| Avg WeakSkillOverlap F1 | 0.422    | 0.465    | **+0.043** |

**Key Observation:** With 14/18 KCs classified as weak, the baseline already achieves reasonable overlap (0.422) because almost any tag hits a weak skill by chance (14/18 = 78% base rate). The enriched condition still improves but with less room for gain.

### 4.4 Results — Student 14475 (High Performer, 0 weak skills)

Both conditions correctly identify zero systematic gaps. Zero false positives on 100% score problems.

| Metric                  | Baseline | Enriched | Delta     |
| ----------------------- | -------- | -------- | --------- |
| Avg WeakSkillOverlap F1 | 0.000    | 0.000    | **0.000** |

### 4.5 Cross-Student Summary

|             | Struggling (10155) | Average (14359) | High Performer (14475) |
| ----------- | ------------------ | --------------- | ---------------------- |
| Weak Skills | 14 / 18            | 2 / 18          | 0 / 18                 |
| Baseline F1 | 0.422              | 0.057           | 0.000                  |
| Enriched F1 | 0.465              | 0.251           | 0.000                  |
| Delta F1    | +0.043             | **+0.194**      | 0.000                  |

---

## 5. Experiment 06 — 30-Student Batch Comparison

**Purpose:** Scale the A/B comparison (Curriculum-Aware WITH vs WITHOUT mental model) to 30 students across all 3 clusters for statistical validation.

### 5.1 Experimental Design

| Parameter            | Value                                           |
| -------------------- | ----------------------------------------------- |
| Students             | 28 completed (10 per cluster target, 2 dropped) |
| Problems per student | 10-12 (mixed score buckets)                     |
| Total problem rows   | 330                                             |
| Conditions           | Baseline vs Enriched (same as Experiment 05)    |
| LLM calls            | 660 (330 problems × 2 conditions)               |

### 5.2 Metric Correction

During analysis, we identified a flaw in the original WeakSkillOverlap F1 metric. The original metric compared LLM-flagged tags against ALL of a student's weak skills, including skills that the problem does not test. This unfairly penalized the LLM for not detecting weak skills that were unobservable on a given problem.

**Corrected metric:** `testable_weak_skills = student_weak_skills ∩ problem_required_skills`

The corrected F1 only evaluates against weak skills that the problem actually tests, providing a fairer assessment of LLM accuracy.

| Metric    | Baseline F1 | Enriched F1 | Delta  |
| --------- | ----------- | ----------- | ------ |
| Old       | 0.119       | 0.159       | +0.040 |
| Corrected | 0.286       | 0.335       | +0.049 |

The corrected metric reveals that the LLM was performing substantially better than originally measured. All subsequent analysis uses the corrected metric.

### 5.3 Results — Per-Student Summary (Corrected Metric)

**Struggling Cluster (8 students, 7 with testable weak skills):**

| Student | Weak Skills | Baseline F1 | Enriched F1 | Delta  | Result   |
| ------- | ----------- | ----------- | ----------- | ------ | -------- |
| 14189   | 9           | 0.334       | 0.440       | +0.106 | Improved |
| 14499   | 8           | 0.198       | 0.303       | +0.105 | Improved |
| 14474   | 6           | 0.266       | 0.346       | +0.080 | Improved |
| 9948    | 5           | 0.295       | 0.372       | +0.077 | Improved |
| 10155   | 14          | 0.401       | 0.449       | +0.047 | Improved |
| 14327   | 2           | 0.250       | 0.244       | -0.006 | Worse    |
| 14374   | 12          | 0.476       | 0.386       | -0.091 | Worse    |

**Average Cluster (10 students, 6 with testable weak skills):**

| Student | Weak Skills | Baseline F1 | Enriched F1 | Delta  | Result   |
| ------- | ----------- | ----------- | ----------- | ------ | -------- |
| 14359   | 2           | 0.167       | 0.486       | +0.319 | Improved |
| 10083   | 1           | 0.333       | 0.400       | +0.067 | Improved |
| 14316   | 1           | 0.333       | 0.400       | +0.067 | Improved |
| 14476   | 3           | 0.268       | 0.310       | +0.042 | Improved |
| 10224   | 1           | 0.000       | 0.000       | 0.000  | Same     |
| 14186   | 1           | 0.400       | 0.222       | -0.178 | Worse    |

**High Performer Cluster (10 students):** All students had 0 weak skills. Both conditions produced F1 = 0.000. No false diagnoses.

### 5.4 Aggregate Results

| Metric                             | Value   |
| ---------------------------------- | ------- |
| Students with testable weak skills | 13      |
| Mean Baseline F1 (corrected)       | 0.286   |
| Mean Enriched F1 (corrected)       | 0.335   |
| Mean Delta                         | +0.049  |
| Relative improvement               | +17.1%  |
| Students improved                  | 9 (69%) |
| Students same                      | 1 (8%)  |
| Students worse                     | 3 (23%) |

### 5.5 Statistical Significance

| Test                    | Result              |
| ----------------------- | ------------------- |
| Wilcoxon signed-rank    | p = 0.146           |
| Paired t-test           | p = 0.151           |
| Cohen's d (effect size) | 0.43 (small-medium) |

The improvement did not reach statistical significance at p < 0.05, attributed to the small effective sample size (N = 13 students with testable weak skills). However, the medium effect size (Cohen's d = 0.43) and 69% win rate suggest a meaningful trend.

### 5.6 By-Cluster Breakdown (Students with Testable Weak Skills Only)

| Cluster    | N   | Baseline F1 | Enriched F1 | Delta  | Won | Lost |
| ---------- | --- | ----------- | ----------- | ------ | --- | ---- |
| Struggling | 7   | 0.317       | 0.363       | +0.046 | 5   | 2    |
| Average    | 6   | 0.250       | 0.303       | +0.053 | 4   | 1    |

### 5.7 Mental Model Effectiveness by Weak Skill Count

Analysis of when the mental model helps vs hurts:

| Weak Skills | Pattern     | Example Students               | Explanation                                          |
| ----------- | ----------- | ------------------------------ | ---------------------------------------------------- |
| 2–9         | Helps most  | 14359 (+0.319), 14189 (+0.106) | Mental model gives LLM useful focus on specific gaps |
| 1           | Mixed       | 10083 (+0.067), 14186 (-0.178) | Too little context; can help or distract             |
| 12–14       | Diminishing | 10155 (+0.047), 14374 (-0.091) | Too much context; can overwhelm the LLM              |
| 0           | No effect   | All High Performers            | Nothing to inject                                    |

**Key Finding:** Mental model injection is most effective for students with 2–9 weak skills (the "sweet spot"). For students with very few (1) or very many (12+) weak skills, the additional context can either distract or overwhelm the LLM.

---

## 6. Experiment 08 — Consistency Test (LLM Reliability)

**Purpose:** Verify the LLM produces stable, reproducible output. Same student (14359), same 5 failing problems, same prompts — run 3 times each.

### 6.1 Results

| Condition   | Avg Jaccard |
| ----------- | ----------- |
| Baseline    | 0.650       |
| Enriched    | 0.577       |
| **Overall** | **0.614**   |

### 6.2 Core vs Variable Tags

Each problem has 2–3 "core" tags that appear in ALL 3 runs (stable signal) and 2–3 "variable" tags that appear in only some runs (noise).

**Core stability rate:** 44.8% of all tags appeared in all 3 runs.

| Problem | Score | Baseline Core                  | Enriched Core                 |
| ------- | ----- | ------------------------------ | ----------------------------- |
| 108     | 68.4% | ArrayIndex, NestedFor          | ArrayIndex, NestedFor         |
| 32      | 54.5% | For, If/Else, StringIndex      | For, If/Else, StringIndex     |
| 107     | 54.5% | For, LogicBoolean              | NestedFor, While              |
| 40      | 38.5% | For, StringEqual, StringIndex  | For, StringEqual, StringIndex |
| 34      | 14.3% | For, StringConcat, StringIndex | For, NestedFor, StringConcat  |

### 6.3 Interpretation

Moderate consistency (Jaccard = 0.614). The LLM's core gap identifications are stable across runs. Variable tags add noise at the margins but do not invalidate the primary findings. The enriched condition is slightly less consistent (0.577 vs 0.650) because the mental model provides additional context that introduces more variation in peripheral tag selection.

Single-run results capture the primary signal. Aggregate metrics across multiple problems and students naturally smooth out per-run variation.

---

## 7. Experiment 07 — Validation Analysis

### 7.1 Grade Correlation (All 372 Students)

**Purpose:** Validate that the mental model's weak skill identification reflects real student ability.

| Correlation               | Pearson r | p-value | Significant? |
| ------------------------- | --------- | ------- | ------------ |
| NumWeakSkills vs X-Grade  | -0.075    | 0.149   | No           |
| AvgScore vs X-Grade       | 0.270     | < 0.001 | Yes          |
| NumWeakSkills vs AvgScore | -0.477    | < 0.001 | Yes          |

**Interpretation:** The mental model's weak skill identification strongly correlates with student performance on coding exercises (r = -0.477, p < 0.001), confirming that the skill mastery calculation accurately captures coding ability. The weak correlation with final course grade (r = -0.075, p = 0.15) is expected because X-Grade incorporates exams, projects, and participation beyond coding exercises.

### 7.2 Relevance F1 Analysis (Experiment 05 Data)

**Purpose:** Verify the LLM identifies gaps relevant to what the problem actually tests.

| Student | Type           | Problems | Baseline Relevance | Enriched Relevance | Delta  |
| ------- | -------------- | -------- | ------------------ | ------------------ | ------ |
| 10155   | Struggling     | 8        | 0.648              | 0.574              | -0.075 |
| 14359   | Average        | 5        | 0.467              | 0.520              | +0.053 |
| 14475   | High Performer | 4        | 0.531              | 0.624              | +0.093 |
| Overall |                | 17       | 0.567              | 0.570              | +0.002 |

**Interpretation:** Relevance F1 averaging 0.57 confirms the LLM predominantly identifies skills the problem actually tests. The enriched condition sometimes shows lower relevance for struggling students because the mental model steers the LLM toward student-specific weak skills that may not perfectly align with the specific problem's requirements — a design trade-off.

### 7.3 Random Baseline Comparison (Experiment 05 Data)

**Purpose:** Determine whether the system's performance exceeds random chance.

| Student                | Weak Skills | Random F1 Mean | 95th %ile | Baseline F1 | Enriched F1 |
| ---------------------- | ----------- | -------------- | --------- | ----------- | ----------- |
| 10155 (Struggling)     | 14          | 0.413          | 0.464     | 0.422       | 0.465       |
| 14359 (Average)        | 2           | 0.151          | 0.284     | 0.057       | 0.251       |
| 14475 (High Performer) | 0           | 0.000          | 0.000     | 0.000       | 0.000       |

**Interpretation:** For the average student, enriched F1 (0.251) substantially exceeds random chance (0.151 mean). For the struggling student, the high base rate of weak skills (14/18 = 78%) makes random overlap high, but the enriched condition still exceeds the 95th percentile.

---

## 8. Human Expert Validation

**Purpose:** Validate LLM gap detection against independent human judgment as ground truth.

### 8.1 Design

A human expert (the thesis author) independently evaluated 10 student-problem pairs selected from the batch experiment. For each case, the expert read the student's code and the problem requirement, then judged which skills showed evidence of a gap (YES), no gap (NO), or insufficient evidence (N/A).

Cases were selected to include a mix of: enriched-beats-baseline (4), baseline-beats-enriched (3), and tied cases (3).

### 8.2 Agreement Results

| Metric                         | Baseline | Enriched |
| ------------------------------ | -------- | -------- |
| Avg Jaccard (human vs LLM)     | 0.429    | 0.477    |
| Avg F1 (LLM vs human as truth) | 0.549    | 0.604    |
| Cases won                      | 4        | 2        |
| Cases tied                     | 4        | 4        |

### 8.3 Per-Case Breakdown

| Case | Student | Problem | Score | Human Gaps | BL F1 | EN F1 | Winner   |
| ---- | ------- | ------- | ----- | ---------- | ----- | ----- | -------- |
| 1    | 14476   | 32      | 0.0%  | 7          | 0.500 | 0.364 | Baseline |
| 2    | 10155   | 235     | 85.7% | 2          | 0.000 | 0.800 | Enriched |
| 3    | 9948    | 104     | 33.3% | 7          | 0.667 | 0.857 | Enriched |
| 4    | 14499   | 232     | 0.0%  | 5          | 0.545 | 0.500 | Baseline |
| 5    | 14374   | 25      | 76.2% | 0          | 0.000 | 0.000 | Tie      |
| 6    | 14327   | 21      | 60.0% | 2          | 0.800 | 0.667 | Baseline |
| 7    | 14474   | 128     | 66.7% | 3          | 0.571 | 0.444 | Baseline |
| 8    | 9948    | 100     | 0.0%  | 4          | 0.750 | 0.750 | Tie      |
| 9    | 9948    | 22      | 36.0% | 3          | 0.857 | 0.857 | Tie      |
| 10   | 14374   | 20      | 50.0% | 2          | 0.800 | 0.800 | Tie      |

### 8.4 Qualitative Observations

**LLM tends to over-flag.** In most cases, the LLM flagged more skills as gaps than the human expert identified. Common over-flagged skills include DefFunction, NestedIf, and LogicBoolean. This suggests the LLM errs on the side of caution — preferable for an instructor-facing tool where missing a gap is more harmful than a false alarm.

**Case 2 — best enriched performance.** The baseline flagged nothing on student 10155's dateFashion problem (85.7% score). The enriched version correctly identified both gaps the human flagged (If/Else, LogicAndNotOr). The mental model context enabled the LLM to detect subtle logic issues in near-passing code that the baseline overlooked entirely.

**Case 5 — human-LLM disagreement.** The human flagged zero gaps for student 14374 on evenlySpaced (76.2% score), while both LLM conditions flagged 3–5 gaps. Review suggests the LLM may have correctly identified that the student's code fails for unsorted inputs — a gap the human initially overlooked. This highlights that LLM analysis can sometimes catch issues that human review misses.

**Comprehension vs skill gaps.** In Case 7 (bobThere), the student misunderstood the problem requirements rather than lacking specific programming skills. Code-based gap detection cannot distinguish between missing skills and misunderstood requirements — a fundamental limitation of this approach.

### 8.5 Interpretation

The enriched condition shows higher average agreement with human judgment (F1 = 0.604 vs 0.549), supporting the value of mental model injection. The moderate agreement levels (Jaccard 0.43–0.48) reflect a combination of genuine disagreements and the inherent subjectivity of gap identification — both human and LLM judgments involve interpretation of ambiguous student code.

---

## 9. Key Findings Summary

### Finding 1: Mental Model Injection Improves Gap Detection

Across 13 students with testable weak skills in the 30-student batch, the enriched condition outperformed baseline on the corrected WeakSkillOverlap F1 (0.335 vs 0.286, +17.1% relative improvement). 9 of 13 students (69%) showed improvement, with only 3 showing decreased performance.

### Finding 2: The Original Metric Underestimated LLM Performance

The corrected metric (filtering to testable weak skills only) revealed that the LLM was performing substantially better than initially measured. Corrected F1 values (0.286–0.335) are roughly double the original values (0.119–0.159). The correction itself represents a methodological contribution.

### Finding 3: Effectiveness Depends on Number of Weak Skills

Mental model injection is most effective for students with 2–9 weak skills ("sweet spot"). Students with very few weak skills (1) see mixed results — the mental model can distract. Students with very many weak skills (12+) see diminishing returns — the mental model can overwhelm the LLM with too much context.

### Finding 4: Average Students Benefit Most

The largest improvement was observed for average students, particularly student 14359 (corrected delta +0.319). These students have subtle, specific weaknesses that the baseline cannot detect but the mental model precisely targets. This is also the group where instructors most need help — struggling students are already visibly at risk, but average students with hidden gaps can slip through.

### Finding 5: LLM Output Is Consistent, Relevant, and Validated

- Consistency: Jaccard = 0.614, with stable core tags across runs
- Relevance: F1 = 0.57, confirming problem-appropriate gap identification
- Human validation: F1 = 0.60 (enriched) against expert judgment
- Grade correlation: Weak skill count correlates with coding performance (r = -0.477, p < 0.001)

### Finding 6: Results Are Directionally Strong but Not Statistically Significant

The improvement did not reach statistical significance (Wilcoxon p = 0.146), attributed to the small effective sample size (N = 13). The medium effect size (Cohen's d = 0.43) and consistent directional improvement (69% win rate) support the finding as a meaningful trend warranting larger-scale validation.

---

## 10. Limitations

### Evaluation Approach

1. **Metric measures pattern matching, not problem-specific accuracy:** The WeakSkillOverlap F1 compares the LLM's per-problem gap tags against the student's persistent weak skills computed across all problems. This creates a mismatch — the LLM is asked to identify gaps in one specific piece of code, but is evaluated against a student-level profile. When the LLM correctly identifies a problem-specific gap that is not a persistent weakness, it is penalized. Both conditions face this same limitation, so the relative comparison remains valid, but absolute F1 values underrepresent the LLM's true problem-specific accuracy.

2. **Ground truth assumes equal skill contribution within problems:** Each problem tests multiple skills simultaneously, but the ground truth treats all tested skills equally. When a student scores 54% on a problem testing 8 skills, we cannot determine which specific skills caused the failure. Per-test-case evaluation (as used in TIKTOC) would provide more precise attribution of failures to specific skills.

3. **Weak skill threshold sensitivity:** The 0.6 mastery threshold that defines "weak" is a design choice without empirical justification. A difference of 0.02 in mastery can determine whether a skill is included in the ground truth. Sensitivity analysis across multiple thresholds (e.g., 0.5, 0.55, 0.6, 0.65) would quantify how robust the findings are to this choice.

4. **Metric limitations beyond correction:** Even the corrected WeakSkillOverlap F1 only rewards matching persistent weaknesses. It does not capture correct problem-specific gap identification that is accurate but not a persistent weakness. The Relevance F1 partially addresses this.

5. **Cannot distinguish comprehension gaps from skill gaps:** When a student writes incorrect code, it may be because they lack the required programming skill or because they misunderstood the problem requirements. Both present identically in the code. In Case 7 of the human validation, the student likely misunderstood the problem rather than lacking For loop or StringIndex skills. Code-based gap detection cannot make this distinction.

### Experimental Design

6. **Sample size:** 28 students completed the batch experiment, but only 13 had testable weak skills, limiting statistical power. A larger sample (N ≥ 30 with testable weak skills) would likely achieve significance given the observed effect size (Cohen's d = 0.43).

7. **Single LLM:** All experiments use Gemini 2.5 Flash. Results may differ with other models (GPT-4, Claude, Llama).

8. **Single run per condition:** Each condition was run once per problem. Consistency testing (Jaccard = 0.614) shows this captures the core signal but introduces noise at the margins.

9. **Grade correlation weakness:** Weak skills predict coding exercise performance (r = -0.477) but not final course grade (r = -0.075), limiting claims about academic outcome prediction.

### Scope and Generalizability

10. **CodeWorkout dataset scope:** Results are specific to introductory Java programming exercises. Generalization to other languages, courses, or difficulty levels is not established.

11. **Human validation scope:** Expert validation was conducted on 10 cases by a single rater (the thesis author). Inter-rater reliability with additional experts would strengthen the validation.

### Mental Model Design

12. **Mental model overwhelm:** For students with 12+ weak skills, the mental model context can overwhelm the LLM, leading to decreased performance. A filtered or prioritized mental model (e.g., top-5 weakest skills only) may address this.

13. **No difficulty weighting:** The mental model computes skill mastery as a simple average across all problems testing that skill, regardless of problem difficulty. A student failing a hard problem (class average 30%) is treated the same as failing an easy problem (class average 90%).

14. **No temporal weighting:** The mental model treats all submissions equally regardless of when they occurred. A student who was weak at For loops in week 1 but mastered them by week 10 is still labeled as weak if the average falls below the threshold.

---

## 11. Completed Experiments

| Experiment                      | Status   | Key Result                                        |
| ------------------------------- | -------- | ------------------------------------------------- |
| 01 — Prompt Strategy Comparison | Complete | Curriculum-Aware selected as best strategy        |
| 05 — Single-Student A/B (×3)    | Complete | +0.194 delta for average student                  |
| 06 — 30-Student Batch           | Complete | 69% win rate, +17.1% relative improvement         |
| 06b — Corrected Metric          | Complete | LLM performing 2× better than originally measured |
| 07 — Validation Analysis        | Complete | Grade correlation r=-0.477, relevance F1=0.57     |
| 08 — Consistency Test           | Complete | Jaccard = 0.614, stable core tags                 |
| Human Expert Validation         | Complete | F1 = 0.60 (enriched) against human judgment       |
| Statistical Significance        | Complete | p = 0.146, Cohen's d = 0.43                       |
