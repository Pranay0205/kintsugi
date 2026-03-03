# Experiment 05: Mental Model Impact Study — Three-Student Comparison

## Overview

This experiment tests whether injecting a student's cognitive profile (mental model)
into the LLM prompt improves knowledge gap detection accuracy compared to analyzing
code in isolation.

**Research Question:** Does providing the LLM with a student's weak skill profile
improve its ability to identify knowledge gaps in student code submissions?

**Method:** Controlled A/B comparison where the only variable is mental model injection.

---

## Experimental Design

### Setup

| Parameter            | Value                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------- |
| LLM                  | Gemini 2.5 Flash                                                                      |
| Temperature          | 0.3                                                                                   |
| Base Prompt          | Curriculum-Aware (with course structure, problem descriptions, KC-constrained output) |
| KC Vocabulary        | 19 exact Knowledge Component names from problem_prompts.csv                           |
| Problems per Student | 12 (selected across score buckets: 100%, partial, 0%)                                 |
| Conditions           | A = Baseline (no mental model), B = Enriched (mental model injected)                  |

### Conditions

**Condition A (Baseline):** The LLM receives the Curriculum-Aware prompt containing
course curriculum structure, problem descriptions, and analysis instructions. It
analyzes student code with no prior knowledge of the student's history or skill profile.

**Condition B (Context-Enriched):** The LLM receives the identical Curriculum-Aware
prompt plus an appended mental model payload containing the student's weak skills
(with mastery scores), strong skills, and prerequisite risk chains derived from
their full submission history.

### Key Constraint

Both conditions use the same student, same problems, same prompt structure, same LLM,
same temperature. The ONLY difference is the presence or absence of the mental model.

### Students Selected

Students were selected as cluster medoids from K-Means clustering (K=3) on skill
mastery vectors derived from the CodeWorkout dataset (372 students, 50 problems).

| Student | Cluster        | X-Grade | Weak Skills (threshold < 0.6)                       |
| ------- | -------------- | ------- | --------------------------------------------------- |
| 10155   | Struggling     | Low     | 14 out of 18 KCs                                    |
| 14359   | Average        | Mid     | 2 out of 18 KCs (StringConcat: 0.578, While: 0.582) |
| 14475   | High Performer | High    | 0 out of 18 KCs                                     |

Each student is the mathematically most representative member of their cluster
(nearest to centroid), minimizing outlier bias in case study selection.

### Mental Model Construction

For each student, the mental model is built from their complete submission history:

1. **Skill Mastery Vector:** Per-KC mastery score computed as mean score across all
   problems requiring that KC (from problem_prompts.csv binary KC weights).
2. **Weak Skill Extraction:** Skills with mastery < 0.6 and at least one attempt.
3. **Prerequisite Risk Chains:** Directed graph of KC dependencies used to identify
   downstream topics at risk due to weak prerequisites.
4. **Payload:** JSON object containing weak skills with scores, strong skills,
   and prerequisite risk chains — appended to the prompt.

### Metrics

**Primary Metric — WeakSkillOverlap F1:**
Measures whether the LLM's predicted KC tags match the student's actual weak skills.

- Precision: Of the KC tags the LLM flagged, how many are actual weak skills?
- Recall: Of the student's actual weak skills, how many did the LLM identify?
- F1: Harmonic mean of precision and recall.

Computed only on failing problems (score < 100%) where gaps are expected.

**Secondary Metric — Perfect Score Correctness:**
For problems where the student scored 100%, both conditions should return zero
knowledge gaps. Flagging gaps on correct code is a false positive.

---

## Results

### Student 14359 — Average (2 weak skills)

**Problem Selection:** 7 perfect (100%), 5 failing (14.3% - 68.4%)

**100% Score Problems (7):**

| Result           | Baseline            | Enriched            |
| ---------------- | ------------------- | ------------------- |
| Correct (0 gaps) | 6 / 7               | 6 / 7               |
| False Positive   | Problem 24 (3 gaps) | Problem 24 (2 gaps) |

**Failing Problems (5) — Per-Problem KC Tags:**

| Problem | Score | Baseline Tags                                              | Enriched Tags                                             | B_F1  | E_F1  |
| ------- | ----- | ---------------------------------------------------------- | --------------------------------------------------------- | ----- | ----- |
| 108     | 68.4% | ArrayIndex, For, LogicBoolean, NestedFor                   | ArrayIndex, For, If/Else, LogicAndNotOr, NestedFor        | 0.000 | 0.000 |
| 32      | 54.5% | For, If/Else, StringIndex                                  | For, If/Else, **StringConcat**, StringIndex, **While**    | 0.000 | 0.571 |
| 107     | 54.5% | For, LogicAndNotOr, LogicBoolean, NestedFor                | For, NestedFor, **While**                                 | 0.000 | 0.400 |
| 40      | 38.5% | For, LogicAndNotOr, NestedFor, StringEqual, StringIndex    | DefFunction, For, LogicBoolean, StringEqual, StringIndex  | 0.000 | 0.000 |
| 34      | 14.3% | DefFunction, For, NestedFor, **StringConcat**, StringIndex | ArrayIndex, For, NestedFor, **StringConcat**, StringIndex | 0.286 | 0.286 |

Bold = matches student's actual weak skills (StringConcat, While).

**Aggregate (Failing Problems):**

| Metric             | Baseline | Enriched | Delta      |
| ------------------ | -------- | -------- | ---------- |
| Avg WeakOverlap F1 | 0.057    | 0.251    | **+0.194** |

**Key Observation:** On problems 32 and 107, the enriched condition correctly
identified StringConcat and While as contributing factors, while the baseline
missed both entirely. The mental model provided the context needed to
pinpoint the narrow set of weak skills.

---

### Student 10155 — Struggling (14 weak skills)

**Problem Selection:** 4 perfect (100%), 8 failing (0% - 85.7%)

**Weak Skills (14):** While (0.044), DefFunction (0.216), StringConcat (0.221),
Math% (0.297), StringLen (0.364), StringIndex (0.400), StringEqual (0.417),
ArrayIndex (0.438), StringFormat (0.477), For (0.488), NestedFor (0.500),
LogicCompareNum (0.538), Math+-\*/ (0.555), If/Else (0.589)

**100% Score Problems (4):**

| Result           | Baseline             | Enriched             |
| ---------------- | -------------------- | -------------------- |
| Correct (0 gaps) | 3 / 4                | 3 / 4                |
| False Positive   | Problem 232 (2 gaps) | Problem 232 (2 gaps) |

**Failing Problems (8) — Per-Problem KC Tags:**

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

| Metric             | Baseline | Enriched | Delta      |
| ------------------ | -------- | -------- | ---------- |
| Avg WeakOverlap F1 | 0.422    | 0.465    | **+0.043** |

**Key Observation:** With 14 out of 18 KCs classified as weak, the baseline
already achieves reasonable overlap (0.422) because almost any tag the LLM
produces hits a weak skill by chance (14/18 = 78% base rate). The enriched
condition still improves but with less room for gain. Qualitatively, the
enriched version produced more targeted tags — for example, on problem 106
it correctly added DefFunction and LogicCompareNum while dropping the
generic LogicBoolean.

---

### Student 14475 — High Performer (0 weak skills)

**Problem Selection:** 8 perfect (100%), 4 failing (72.0% - 93.3%)

**100% Score Problems (8):**

| Result           | Baseline | Enriched |
| ---------------- | -------- | -------- |
| Correct (0 gaps) | 8 / 8    | 8 / 8    |
| False Positive   | None     | None     |

**Failing Problems (4) — Per-Problem KC Tags:**

| Problem | Score | Baseline Tags                                      | Enriched Tags                                         | Match |
| ------- | ----- | -------------------------------------------------- | ----------------------------------------------------- | ----- |
| 38      | 93.3% | For, LogicAndNotOr, StringIndex                    | For, StringIndex                                      | DIFF  |
| 118     | 90.9% | ArrayIndex, If/Else                                | ArrayIndex, If/Else                                   | SAME  |
| 46      | 72.2% | ArrayIndex, For, If/Else, LogicAndNotOr, NestedFor | ArrayIndex, For, If/Else, LogicAndNotOr, LogicBoolean | DIFF  |
| 101     | 72.0% | DefFunction, For, Math%, Math+-\*/                 | If/Else, LogicCompareNum, Math+-\*/                   | DIFF  |

**Aggregate (Failing Problems):**

| Metric             | Baseline | Enriched | Delta     |
| ------------------ | -------- | -------- | --------- |
| Avg WeakOverlap F1 | 0.000    | 0.000    | **0.000** |

**Key Observation:** With zero weak skills, WeakSkillOverlap is 0.0 for both
conditions by definition — there is no target to overlap with. The LLM still
identifies gaps on the 4 failing problems (scores 72-93%), but these represent
occasional mistakes rather than persistent weaknesses. Both conditions perform
identically on 100% problems with zero false positives — the cleanest
confirmation that the system does not hallucinate gaps where none exist.

---

## Cross-Student Comparison

|                         | Struggling (10155) | Average (14359) | High Performer (14475) |
| ----------------------- | ------------------ | --------------- | ---------------------- |
| Weak Skills             | 14 / 18            | 2 / 18          | 0 / 18                 |
| Perfect Problems        | 4 / 12             | 7 / 12          | 8 / 12                 |
| Failing Problems        | 8                  | 5               | 4                      |
| Baseline WeakOverlap F1 | 0.422              | 0.057           | 0.000                  |
| Enriched WeakOverlap F1 | 0.465              | 0.251           | 0.000                  |
| **Delta F1**            | **+0.043**         | **+0.194**      | **0.000**              |
| False Positives on 100% | 1 (P232)           | 1 (P24)         | 0                      |

---

## Key Findings

### Finding 1: Mental Model Injection Improves Gap Detection Accuracy

The context-enriched condition outperformed the baseline on WeakSkillOverlap F1
for both students with identified weak skills. The improvement was largest for
the average student (+0.194) and positive but smaller for the struggling
student (+0.043).

### Finding 2: The Effect Is Strongest for Average Students

The average student (14359) showed the largest improvement because the baseline
had insufficient context to identify the narrow set of 2 weak skills (11% base
rate of random overlap). The mental model provided precisely the context needed.
For the struggling student (14359), the high number of weak skills (78% base
rate) meant the baseline achieved reasonable overlap through breadth alone,
leaving less room for improvement.

### Finding 3: High Performers Require No Mental Model

With zero persistent weak skills, the mental model has nothing meaningful to
inject. Both conditions correctly identified zero systematic gaps. This
validates that the system does not introduce false diagnoses for strong students.

### Finding 4: Both Conditions Handle Perfect Scores Well

Across all three students, the LLM correctly returned zero gaps on 17 out of
19 perfect-score problems (89.5%). The two false positives (problems 24 and 232)
occurred for both conditions, suggesting a problem-specific LLM confusion rather
than a systematic flaw.

### Finding 5: The Enriched Condition Produces Qualitatively Different Tags

On 7 out of 8 failing problems where both conditions were compared, the enriched
condition produced different KC tags than the baseline. The enriched tags more
frequently included the student's actual weak skills. For example, on problem 32
for student 14359, the enriched version correctly added StringConcat and While
(the student's two weak skills) while the baseline detected neither.

---

## Limitations

1. **Sample Size:** Three students (one per cluster medoid) provide illustrative
   case studies but not statistical significance. The batch experiment
   (30 students) addresses this.

2. **WeakSkillOverlap Metric Sensitivity:** For students with many weak skills,
   high overlap can occur by chance. Future work could use a chance-corrected
   metric (e.g., Cohen's Kappa against random baseline).

3. **Problem 232 False Positive:** Both conditions flagged gaps on correct code
   for this problem across two students, suggesting a problem-specific
   ambiguity that confuses the LLM.

4. **Threshold Sensitivity:** Weak skill threshold of 0.6 is a design choice.
   Different thresholds would produce different numbers of weak skills and
   potentially different overlap results.

5. **Single LLM Run:** Each condition was run once per problem. Running 3x and
   averaging would measure consistency, but triples the cost.

---

## Implication for Thesis

These three case studies establish the mechanism: mental model injection helps
the LLM identify specific, targeted knowledge gaps that it misses without
context. The effect is most pronounced for students whose weaknesses are
not obvious from individual code submissions alone (the average student).

The subsequent batch experiment (30 students, 10 per cluster) will determine
whether this effect replicates across students and whether the per-cluster
pattern holds at scale.
