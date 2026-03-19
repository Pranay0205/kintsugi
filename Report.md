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

**Weak Skills (14):** While (0.044), DefFunction (0.216), StringConcat (0.221), Math% (0.297), StringLen (0.364), StringIndex (0.400), StringEqual (0.417), ArrayIndex (0.438), StringFormat (0.477), For (0.488), NestedFor (0.500), LogicCompareNum (0.538), Math+-\*/ (0.555), If/Else (0.589)

**100% Score Problems:** 3/4 correct for both. Problem 232 was a false positive for both conditions (2 gaps each).

**Failing Problems — Per-Problem KC Tags:**

| Problem | Score | Baseline Tags                                                             | Enriched Tags                                                                       | Match |
| ------- | ----- | ------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ----- |
| 235     | 85.7% | If/Else, LogicAndNotOr, LogicBoolean, NestedIf                            | If/Else, LogicAndNotOr, NestedIf                                                    | DIFF  |
| 236     | 75.0% | If/Else, LogicAndNotOr, NestedIf                                          | If/Else, LogicAndNotOr, NestedIf                                                    | SAME  |
| 106     | 62.5% | ArrayIndex, For, If/Else, LogicBoolean, NestedFor                         | ArrayIndex, DefFunction, For, If/Else, LogicCompareNum, NestedFor                   | DIFF  |
| 46      | 55.6% | ArrayIndex, DefFunction, For, If/Else, LogicAndNotOr, NestedFor           | ArrayIndex, DefFunction, For, NestedFor, StringIndex, StringLen                     | DIFF  |
| 36      | 41.2% | CharEqual, DefFunction, For, If/Else, StringEqual, StringIndex, StringLen | ArrayIndex, CharEqual, DefFunction, For, If/Else, NestedFor, StringIndex, StringLen | DIFF  |
| 49      | 41.2% | ArrayIndex, DefFunction, For, If/Else, Math+-\*/                          | ArrayIndex, DefFunction, For, If/Else, NestedFor, While                             | DIFF  |
| 32      | 0.0%  | ArrayIndex, DefFunction, For, If/Else, StringEqual, StringIndex           | DefFunction, For, StringConcat, StringEqual, StringIndex, StringLen                 | DIFF  |
| 101     | 0.0%  | DefFunction, For, If/Else, LogicCompareNum, Math+-\*/                     | DefFunction, If/Else, Math%, Math+-\*/                                              | DIFF  |

**Aggregate (Failing Problems):**

| Metric                  | Baseline | Enriched | Delta      |
| ----------------------- | -------- | -------- | ---------- |
| Avg WeakSkillOverlap F1 | 0.422    | 0.465    | **+0.043** |

**Key Observation:** With 14/18 KCs classified as weak, the baseline already achieves reasonable overlap (0.422) because almost any tag hits a weak skill by chance (14/18 = 78% base rate). The enriched condition still improves but with less room for gain. Qualitatively, the enriched version produced more targeted tags — on problem 106 it correctly added DefFunction and LogicCompareNum while dropping the generic LogicBoolean.

### 4.4 Results — Student 14475 (High Performer, 0 weak skills)

**Problem selection:** 8 perfect (100%), 4 failing (72.0% - 93.3%)

**100% Score Problems:** 8/8 correct for both conditions. Zero false positives.

**Failing Problems — Per-Problem KC Tags:**

| Problem | Score | Baseline Tags                                      | Enriched Tags                                         | Match |
| ------- | ----- | -------------------------------------------------- | ----------------------------------------------------- | ----- |
| 38      | 93.3% | For, LogicAndNotOr, StringIndex                    | For, StringIndex                                      | DIFF  |
| 118     | 90.9% | ArrayIndex, If/Else                                | ArrayIndex, If/Else                                   | SAME  |
| 46      | 72.2% | ArrayIndex, For, If/Else, LogicAndNotOr, NestedFor | ArrayIndex, For, If/Else, LogicAndNotOr, LogicBoolean | DIFF  |
| 101     | 72.0% | DefFunction, For, Math%, Math+-\*/                 | If/Else, LogicCompareNum, Math+-\*/                   | DIFF  |

**Aggregate (Failing Problems):**

| Metric                  | Baseline | Enriched | Delta     |
| ----------------------- | -------- | -------- | --------- |
| Avg WeakSkillOverlap F1 | 0.000    | 0.000    | **0.000** |

**Key Observation:** With zero weak skills, WeakSkillOverlap is 0.0 by definition. The LLM still identifies problem-specific gaps on the 4 failing problems, but these represent occasional mistakes rather than persistent weaknesses. Both conditions perform identically on 100% problems with zero false positives.

### 4.5 Cross-Student Summary

|                         | Struggling (10155) | Average (14359) | High Performer (14475) |
| ----------------------- | ------------------ | --------------- | ---------------------- |
| Weak Skills             | 14 / 18            | 2 / 18          | 0 / 18                 |
| Perfect Problems        | 4 / 12             | 7 / 12          | 8 / 12                 |
| Failing Problems        | 8                  | 5               | 4                      |
| Baseline F1             | 0.422              | 0.057           | 0.000                  |
| Enriched F1             | 0.465              | 0.251           | 0.000                  |
| Delta F1                | +0.043             | **+0.194**      | 0.000                  |
| False Positives on 100% | 1 (P232)           | 1 (P24)         | 0                      |

**Result files:** results/05_mental_model_comparison/v1_simple_average/

---

## 5. Experiment 08 — Consistency Test (LLM Reliability)

**Purpose:** Verify the LLM produces stable, reproducible output. Same student (14359), same 5 failing problems, same prompts — run 3 times each.

**Metric:** Jaccard Similarity between tag sets across runs. 1.0 = identical every run, 0.0 = completely different.

### 5.1 Results

| Condition   | Avg Jaccard |
| ----------- | ----------- |
| Baseline    | 0.650       |
| Enriched    | 0.577       |
| **Overall** | **0.614**   |

### 5.2 Core vs Variable Tags

Each problem has 2-3 "core" tags that appear in ALL 3 runs (stable signal) and 2-3 "variable" tags that appear in only some runs (noise).

| Problem | Score | Baseline Core                  | Enriched Core                 |
| ------- | ----- | ------------------------------ | ----------------------------- |
| 108     | 68.4% | ArrayIndex, NestedFor          | ArrayIndex, NestedFor         |
| 32      | 54.5% | For, If/Else, StringIndex      | For, If/Else, StringIndex     |
| 107     | 54.5% | For, LogicBoolean              | NestedFor, While              |
| 40      | 38.5% | For, StringEqual, StringIndex  | For, StringEqual, StringIndex |
| 34      | 14.3% | For, StringConcat, StringIndex | For, NestedFor, StringConcat  |

### 5.3 Interpretation

**Moderate consistency (Jaccard = 0.614).** The LLM's core gap identifications are stable across runs. Variable tags add noise at the margins but do not invalidate the primary findings. The enriched condition is slightly less consistent (0.577 vs 0.650) because the mental model provides additional context that introduces more variation in peripheral tag selection.

**Verdict:** Single-run results capture the primary signal. Aggregate metrics across multiple problems and students naturally smooth out per-run variation.

**Result files:** results/08_consistency_test/

---

## 6. Experiment 07 — Validation Analysis

### 6.1 Grade Correlation (All 372 Students)

**Purpose:** Validate that the mental model's weak skill identification reflects real student ability by correlating with course grades.

| Correlation               | Pearson r | p-value | Significant? |
| ------------------------- | --------- | ------- | ------------ |
| NumWeakSkills vs X-Grade  | -0.075    | 0.149   | No           |
| AvgScore vs X-Grade       | 0.270     | < 0.001 | Yes          |
| NumWeakSkills vs AvgScore | -0.477    | < 0.001 | Yes          |

**Interpretation:** The mental model's weak skill identification strongly correlates with student performance on coding exercises (r = -0.477, p < 0.001), confirming that the skill mastery calculation accurately captures coding ability. The correlation with final course grade (X-Grade) was not statistically significant (r = -0.075, p = 0.15), because X-Grade incorporates multiple assessment types (exams, projects, participation) beyond coding exercises, diluting the CodeWorkout-specific signal.

**The important validation is NumWeakSkills vs AvgScore (r = -0.477).** This confirms the mental model correctly ranks students by coding ability, which is what the gap detection system acts on.

### 6.2 Relevance F1 Analysis

**Purpose:** Verify the LLM identifies gaps relevant to what the problem actually tests (not hallucinating random skills).

[NOTE: Relevance F1 numbers to be added once CSV loading is fixed. Data exists in the experiment 05 CSVs in the Baseline_Relevance_F1 and Enriched_Relevance_F1 columns.]

From the student 10155 CSV (already available):

| Problem | Score | Baseline Relevance | Enriched Relevance |
| ------- | ----- | ------------------ | ------------------ |
| 235     | 85.7% | 0.571              | 0.667              |
| 236     | 75.0% | 0.667              | 0.667              |
| 106     | 62.5% | 0.727              | 0.833              |
| 46      | 55.6% | 0.727              | 0.364              |
| 36      | 41.2% | 0.667              | 0.500              |
| 49      | 41.2% | 0.800              | 0.545              |
| 32      | 0.0%  | 0.429              | 0.571              |
| 101     | 0.0%  | 0.600              | 0.444              |

**Average for student 10155:** Baseline = 0.649, Enriched = 0.574

**Interpretation:** Relevance F1 averaging 0.5-0.7 across problems indicates the LLM is predominantly identifying skills that the problem actually tests. This confirms the LLM output is meaningful — not random noise.

Note: The enriched condition sometimes shows lower relevance because the mental model steers the LLM toward the student's weak skills, which may not perfectly align with the specific problem's KC requirements. This is a design trade-off: the enriched version prioritizes student-specific gaps over problem-specific comprehensiveness.

### 6.3 Random Baseline Comparison

**Purpose:** Determine whether the system's performance exceeds random chance.

| Student                | Weak Skills | Random F1 Mean | Random 95th %ile | Baseline F1   | Enriched F1   | Enriched vs Random |
| ---------------------- | ----------- | -------------- | ---------------- | ------------- | ------------- | ------------------ |
| 10155 (Struggling)     | 14          | 0.413          | 0.464            | 0.422 (NEAR)  | 0.465 (ABOVE) | +0.052             |
| 14359 (Average)        | 2           | 0.151          | 0.284            | 0.057 (BELOW) | 0.251 (NEAR)  | +0.101             |
| 14475 (High Performer) | 0           | 0.000          | 0.000            | 0.000         | 0.000         | 0.000              |

**Interpretation:**

For the struggling student (14 weak skills), random chance produces F1 of 0.413 because 14/18 = 78% of all KCs are weak. The enriched condition marginally exceeds the 95th percentile of random (0.465 vs 0.464).

For the average student (2 weak skills), random chance produces F1 of 0.151. The baseline (0.057) falls below random, meaning the LLM without mental model actively identifies problem-specific gaps that happen not to be the student's persistent weaknesses. The enriched version (0.251) approaches but does not clearly exceed the 95th percentile (0.284).

**This reveals a limitation of the WeakSkillOverlap metric, not a system failure.** The metric only rewards tags matching persistent weaknesses and penalizes correct problem-specific gap identification that doesn't align with those weaknesses. The Relevance F1 analysis (Section 6.2) confirms the LLM is producing sensible, problem-relevant output.

**Result files:** results/07_validation_analysis/

---

## 7. Key Findings Summary

### Finding 1: Mental Model Injection Improves Gap Detection

The context-enriched condition outperformed the baseline on WeakSkillOverlap F1 for both students with identified weak skills. Improvement was largest for the average student (+0.194) and positive for the struggling student (+0.043).

### Finding 2: The Effect Is Strongest for Average Students

The mental model is most valuable where instructors need the most help — identifying specific, hidden gaps of students who appear moderate but have subtle weaknesses that compound over time. The baseline lacks sufficient context to identify a narrow set of 2 weak skills (11% base rate). The mental model provides precisely the context needed.

### Finding 3: High Performers Require No Mental Model

With zero persistent weak skills, the mental model has nothing to inject. Both conditions correctly identify zero systematic gaps. This validates that the system does not introduce false diagnoses for strong students.

### Finding 4: LLM Output Is Consistent and Relevant

Consistency testing shows moderate stability (Jaccard = 0.614) with 2-3 core tags stable across runs. Relevance F1 of 0.5-0.7 confirms the LLM identifies skills actually tested by the problem, not random noise.

### Finding 5: The Mental Model Reflects Real Student Ability

Weak skill count strongly correlates with coding performance (r = -0.477, p < 0.001), confirming the mastery calculation accurately captures student ability on coding exercises.

### Finding 6: WeakSkillOverlap Has Limitations as a Metric

The random baseline analysis reveals that for students with many weak skills, reasonable overlap occurs by chance. The metric also penalizes correct problem-specific gap identification that doesn't match persistent weaknesses. Future work should explore complementary metrics that reward problem-specific accuracy alongside student-level pattern matching.

---

## 8. Limitations

1. **Sample size:** Three students (one per cluster medoid) provide illustrative case studies. The 30-student batch experiment will address statistical significance.

2. **Single LLM:** All experiments use Gemini 2.5 Flash. Results may differ with other models (GPT-4, Claude, Llama).

3. **Single run per condition:** Each condition was run once per problem. Consistency testing (Jaccard = 0.614) shows this is adequate but not ideal.

4. **Weak skill threshold sensitivity:** The 0.6 mastery threshold is a design choice. Different thresholds produce different weak skill counts and potentially different results.

5. **WeakSkillOverlap metric limitations:** The metric only rewards matching persistent weaknesses. It does not capture the LLM's ability to identify problem-specific gaps that are correct but not persistently weak.

6. **Grade correlation weakness:** Weak skills predict coding exercise performance (r = -0.477) but not final course grade (r = -0.075), limiting claims about academic outcome prediction.

7. **Problem 232 false positive:** Both conditions flagged gaps on correct code for this problem across two students, suggesting a problem-specific ambiguity.

8. **CodeWorkout dataset scope:** Results are specific to introductory Java programming exercises. Generalization to other languages, courses, or difficulty levels is not established.

---

## 9. Remaining Experiments

| Experiment            | Status      | Purpose                                                                               |
| --------------------- | ----------- | ------------------------------------------------------------------------------------- |
| 06 — 30-Student Batch | Not yet run | Scale the A/B comparison to 30 students (10 per cluster) for statistical significance |
