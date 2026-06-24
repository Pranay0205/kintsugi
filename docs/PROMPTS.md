# KCDP Diagnostic Prompt — Reference Document

The Knowledge Component Diagnostic Prompt (KCDP) is a single-turn, stateless text prompt that instructs a large language model to act as an expert CS1 instructor, read a student's Java code submission, and return a flat list of Knowledge Component (KC) gaps in JSON. It was run on **Gemini 2.5 Flash** (`gemini-2.5-flash`, temperature 0.3, no other decoding parameters set), with **DeepSeek-V3** (`deepseek-chat`, same temperature) used as a cross-model validation in the ablation study. The prompt was issued once per (student, problem) pair for every non-perfect submission; each call is independent with no conversation history or system instruction. The headline result — problem-level F1 = 0.839, Cohen's κ = 0.557 on 372 non-perfect submissions across 10 students — was produced by this prompt in its default configuration (`rules_mode="full"`, `kc_mode="per_problem"`). This document is the full version of the prompt summarised in Chapter 3 of the thesis; every piece of text below is copied verbatim from the source files listed at the bottom.

---

## Structure

The prompt has ten components assembled top-to-bottom into a single string. Six are fully static (identical across every call); four are templated and filled at call time from `problem_prompts.csv` and the student submission file.

| # | Component | Static / Templated |
|---|---|---|
| 1 | Role declaration | Static |
| 2 | Problem context | Templated |
| 3 | KC definitions (all 18) | Static |
| 4 | Required KCs for this problem | Templated |
| 5 | Tagging hierarchy | Static |
| 6 | Redundancy check | Static |
| 7 | Disambiguation rules (all 14) | Static (ablatable) |
| 8 | Critical rules | Static |
| 9 | Output format (JSON schema) | Static |
| 10 | Student code | Templated |

> **Note on component count.** The prompt source file (`lib/v3_prompt.py`) header lists nine components, folding the Redundancy Check into the Tagging Hierarchy. The thesis and `v3_prompt_spec.md` both treat them as separate, giving ten. Both counts refer to the same prompt text.

---

## Component 1 — Role Declaration

Opens the prompt with a single persona instruction. This establishes the evaluative frame: the model should reason like an instructor diagnosing gaps, not a grader assigning scores.

```
You are an expert CS1 instructor analyzing a single student Java code submission to identify knowledge gaps.
```

---

## Component 2 — Problem Context

Provides the problem's metadata — numeric IDs, the verbatim problem statement the student was asked to solve (`requirement`), and the student's score. The score lets the model calibrate severity: a near-perfect score suggests a minor gap; zero suggests a fundamental one.

**Template** (variables filled at call time from `problem_prompts.csv` and the student submission):

```
PROBLEM CONTEXT:
{
  "problem_id": {problem_id},
  "assignment_id": {assignment_id},
  "requirement": "{requirement}",
  "student_score": {score}
}
```

**Filled-in example** (Problem 1, Assignment 439; score is hypothetical):

```
PROBLEM CONTEXT:
{
  "problem_id": 1,
  "assignment_id": 439,
  "requirement": "Write a function in Java that implements the following logic: Given 2 ints, a and b, return their sum. However, sums in the range 10..19 inclusive, are forbidden, so in that case just return 20.",
  "student_score": 0.75
}
```

---

## Component 3 — KC Definitions

Defines all 18 Knowledge Components used in the course. Each entry specifies a `category`, a `type` (`structural` or `specific`), and a `gap_signal` describing what a gap looks like in student code. This block is identical on every call regardless of which KCs a given problem tests.

```
KC DEFINITIONS:
Below are all 18 Knowledge Components (KCs) used in this course. Each includes what a gap looks like in student code.

{
  "If/Else": {
    "category": "Control Flow",
    "type": "structural",
    "gap_signal": "Tag when the STRUCTURE is wrong: missing branches that the problem requires, wrong order of tests, a case that is never handled, two sequential ifs where if/else was needed. Do NOT tag for missing else when a simple if-with-early-return is cleaner. Do NOT tag when the condition inside the if is wrong but the branching structure is correct — that belongs to a Logic KC."
  },
  "NestedIf": {
    "category": "Control Flow",
    "type": "structural",
    "gap_signal": "Tag only if the code actually contains nested ifs and uses them incorrectly (wrong nesting order, conditions at wrong level). Do NOT tag 'they should have nested' — only tag what the student actually wrote."
  },
  "While": {
    "category": "Loops",
    "type": "structural",
    "gap_signal": "Tag when the loop structure itself is wrong: wrong stopping condition, never updates the loop variable, infinite loop. Do NOT tag if the problem does not require a while loop and the student did not use one. Do NOT tag if the loop structure is fine but the logic inside it is wrong."
  },
  "For": {
    "category": "Loops",
    "type": "structural",
    "gap_signal": "Tag when the loop structure is wrong: wrong initialization, wrong update expression, loop variable does not iterate correctly. Off-by-one in the termination condition belongs to LogicCompareNum, not For."
  },
  "NestedFor": {
    "category": "Loops",
    "type": "structural",
    "gap_signal": "Tag only if code contains nested loops and uses them incorrectly (wrong inner bounds, reusing outer variable, wrong nesting order). Do NOT tag if the problem does not require nested loops. Do NOT infer 'the student would struggle with nested loops' — only tag what is actually in the code."
  },
  "Math+-*/": {
    "category": "Math",
    "type": "specific",
    "gap_signal": "Tag when the student uses the wrong arithmetic operation or gets arithmetic logic wrong: dividing when they should multiply, missing integer-division truncation, wrong order of operations."
  },
  "Math%": {
    "category": "Math",
    "type": "specific",
    "gap_signal": "Tag when the student needs modulo and does not use it, or uses it wrong: checking divisibility with / instead of %, wrong modulo base, misunderstanding what % returns."
  },
  "LogicAndNotOr": {
    "category": "Logic",
    "type": "specific",
    "gap_signal": "Tag when the student combines booleans wrong: uses && where || was needed, inverts a condition incorrectly with !, misses a case when chaining compound conditions, wrong short-circuit logic."
  },
  "LogicCompareNum": {
    "category": "Logic",
    "type": "specific",
    "gap_signal": "Tag for any numeric comparison bug: wrong direction (< vs >), off-by-one at boundary (< vs <=), enumerating values (day==1||day==2||day==3) instead of using ranges (day>=1 && day<=5), comparing when equality was needed or vice versa."
  },
  "LogicBoolean": {
    "category": "Logic",
    "type": "specific",
    "gap_signal": "Tag for: if (x = true) (assignment instead of comparison), returning true/false in the wrong branch, unnecessary if (bool == true) revealing misunderstanding of boolean type, using 0/1 instead of true/false."
  },
  "StringFormat": {
    "category": "Strings",
    "type": "specific",
    "gap_signal": "Tag when the student cannot produce the expected output format even when their logic is close: wrong spacing, missing separators, wrong order of concatenated pieces in the final output string."
  },
  "StringConcat": {
    "category": "Strings",
    "type": "specific",
    "gap_signal": "Tag when concatenation is missing, in wrong order, or produces wrong result. Not about output format (that is StringFormat) — about the mechanical act of joining strings."
  },
  "StringIndex": {
    "category": "Strings",
    "type": "specific",
    "gap_signal": "Tag for wrong index, index out of bounds, off-by-one in string position, using wrong substring bounds."
  },
  "StringLen": {
    "category": "Strings",
    "type": "specific",
    "gap_signal": "Tag when the student confuses .length() method with .length property (Java arrays), or uses wrong length value for substring bounds, or does not account for zero-based indexing with length."
  },
  "StringEqual": {
    "category": "Strings",
    "type": "specific",
    "gap_signal": "Tag when the student uses == on strings instead of .equals(), or compares the wrong parts of strings. Do NOT tag for numeric comparisons — that is LogicCompareNum."
  },
  "CharEqual": {
    "category": "Strings",
    "type": "specific",
    "gap_signal": "Tag when comparison at the character level is wrong: comparing wrong char position, wrong char literal, confusing char with String type."
  },
  "ArrayIndex": {
    "category": "Arrays",
    "type": "specific",
    "gap_signal": "Tag for out-of-bounds access, off-by-one in array indexing, wrong index variable, confusing index with value stored at that index."
  },
  "DefFunction": {
    "category": "Functions",
    "type": "specific",
    "gap_signal": "Tag when the problem asks for a specific helper method and the student's helper is missing, incomplete, has wrong signature, or has broken logic inside it."
  }
}
```

---

## Component 4 — Required KCs for This Problem

Tells the model which KCs the problem was designed to test, drawn from the Q-matrix in `problem_prompts.csv`. This is a prior, not a constraint: the prompt explicitly permits tagging KCs outside the list if the student's code reveals them. In the ablation `full_vocab` condition (`kc_mode="full_vocab"`), this section is replaced by the full 18-KC vocabulary with no shortlist.

**Template** (default `kc_mode="per_problem"`; `{required_kcs}` is a comma-separated list of KC names):

```
REQUIRED KCs FOR THIS PROBLEM: [{required_kcs}]
These are the KCs this problem is designed to test. Check these first. However, if the student's code reveals gaps in other KCs not on this list, tag those too.
```

**Filled-in example** (Problem 1, Assignment 439 — required KCs from Q-matrix: If/Else, Math+-\*/, LogicAndNotOr, LogicCompareNum):

```
REQUIRED KCs FOR THIS PROBLEM: [If/Else, Math+-*/, LogicAndNotOr, LogicCompareNum]
These are the KCs this problem is designed to test. Check these first. However, if the student's code reveals gaps in other KCs not on this list, tag those too.
```

---

## Component 5 — Tagging Hierarchy (Specific Before Structural)

Establishes the core disambiguation principle: structural KCs (If/Else, NestedIf, While, For, NestedFor) are tags of last resort. The model must always prefer a specific KC (Logic, Math, String, Array, Function) when one explains the error. Four inline examples illustrate the rule before the worked examples in Component 6.

```
TAGGING HIERARCHY — CHECK SPECIFIC BEFORE STRUCTURAL:
KCs marked "structural" (If/Else, NestedIf, While, For, NestedFor) are tags of LAST RESORT.
Always check "specific" KCs first (Logic, Math, String, Array, Function).
If a specific KC explains the error, tag ONLY the specific KC. Do NOT also tag the structural KC.
Tag a structural KC only when the structure itself is the problem and no specific KC explains it.

Examples:
- Wrong condition inside an if-statement → LogicCompareNum or LogicBoolean, NOT If/Else
- Wrong loop boundary value → LogicCompareNum, NOT For
- Wrong arithmetic inside a loop body → Math+-*/, NOT For
- Student uses && where || needed inside an if → LogicAndNotOr, NOT If/Else
```

---

## Component 6 — Redundancy Check

Provides worked examples for each of the five structural KCs, each showing a CORRECT and a WRONG tag set for the same scenario. This operationalises the tagging hierarchy from Component 5 with concrete cases the model can pattern-match against. A final sub-section lists conditions under which structural tags *are* legitimate.

```
REDUNDANCY CHECK — apply before finalizing your tags:
For every structural KC (If/Else, NestedIf, While, For, NestedFor) in your list, ask: "If I remove this tag, does my diagnosis lose any information?" If the answer is no — if a specific KC already explains the error — drop the structural tag. A structural tag that adds no new information is wrong, not cautious.

If/Else redundancy:
- Student writes if(day==1||day==2||day==3) instead of if(day>=1 && day<=5)
- CORRECT: ["LogicCompareNum"] — the comparison is wrong, the if-structure is fine
- WRONG: ["LogicCompareNum", "If/Else"]

For redundancy:
- Student writes for(int i=0; i<arr.length; i++) but uses arr[i+1] without bounds check inside
- CORRECT: ["ArrayIndex"] — the array access is wrong, the loop structure is fine
- WRONG: ["ArrayIndex", "For"]
- Student writes for(int i=0; i<10; i++) when it should be i<=10
- CORRECT: ["LogicCompareNum"] — the boundary comparison is wrong, the loop structure is fine
- WRONG: ["LogicCompareNum", "For"]

While redundancy:
- Student writes while(x > 0) but does wrong arithmetic on x inside the loop body
- CORRECT: ["Math+-*/"] — the math is wrong, the while-loop structure is fine
- WRONG: ["Math+-*/", "While"]

NestedIf redundancy:
- Student has if inside if, but the inner condition uses == instead of >=
- CORRECT: ["LogicCompareNum"] — the comparison is wrong, the nesting structure is fine
- WRONG: ["LogicCompareNum", "NestedIf"]

NestedFor redundancy:
- Student has nested loops but uses wrong array index in inner loop body
- CORRECT: ["ArrayIndex"] — the index is wrong, the nesting structure is fine
- WRONG: ["ArrayIndex", "NestedFor"]

When TO tag structural KCs (not redundant):
- If/Else: student uses two separate ifs where if/else was needed, so both branches execute
- For: student writes i++ when it should be i+=2, or initializes i=1 instead of i=0
- While: student never updates the loop variable, causing infinite loop
- NestedIf: student puts conditions at the wrong nesting level
- NestedFor: student reuses the outer loop variable in the inner loop
```

---

## Component 7 — Disambiguation Rules (All 14)

Provides 14 KC-vs-KC tie-breaker rules. When two KCs both seem to apply to the same error, the model consults these rules to pick the correct one. This block is ablatable: `rules_mode="reduced"` keeps only rules 1, 2, 3, and 13 (the four If/Else and inter-Logic disambiguators, at zero-based indices 0, 1, 2, 12); `rules_mode="none"` omits this entire section.

The section header appears in the prompt as:

```
DISAMBIGUATION RULES:
When two KCs seem applicable, use these rules to pick the correct one.
```

followed by the 14 rules as a JSON array. Each rule is listed individually below, verbatim from `DISAMBIGUATION_RULES` in `lib/v3_prompt.py`:

**Rule 1 — LogicCompareNum vs If/Else**
```
LogicCompareNum vs If/Else — If the student writes day==1||day==2||day==3 instead of day>=1&&day<=5, tag LogicCompareNum. The if-statement structure is correct, the comparison inside it is wrong.
```

**Rule 2 — LogicBoolean vs If/Else**
```
LogicBoolean vs If/Else — If the student writes vacation==false instead of !vacation, or uses = instead of ==, tag LogicBoolean. The student misunderstands boolean values, not branching structure.
```

**Rule 3 — LogicAndNotOr vs If/Else**
```
LogicAndNotOr vs If/Else — If the student uses && where || was needed or misses parentheses on grouped conditions, tag LogicAndNotOr. The branching structure is fine, the boolean composition is wrong.
```

**Rule 4 — LogicCompareNum vs For**
```
LogicCompareNum vs For — Off-by-one in a loop termination condition (< vs <=) is LogicCompareNum. The loop structure is correct, the comparison value is wrong. Tag For only when init, update, or overall structure is broken.
```

**Rule 5 — Math+-\*/ vs For**
```
Math+-*/ vs For — Wrong arithmetic inside a loop body is Math+-*/. Wrong increment in the for-update (i+=1 when it should be i+=2) is For, because the update is part of loop structure.
```

**Rule 6 — StringEqual vs LogicCompareNum**
```
StringEqual vs LogicCompareNum — String comparison with == or .equals() is StringEqual. Numeric comparison with <, >, == between numbers is LogicCompareNum. Never interchangeable.
```

**Rule 7 — CharEqual vs StringEqual**
```
CharEqual vs StringEqual — charAt() comparisons are CharEqual. Full-string .equals() comparisons are StringEqual.
```

**Rule 8 — StringIndex vs StringLen**
```
StringIndex vs StringLen — Wrong position in charAt()/substring() is StringIndex. Wrong .length() usage or confusing .length with .length() is StringLen.
```

**Rule 9 — StringConcat vs StringFormat**
```
StringConcat vs StringFormat — Failing to join strings mechanically is StringConcat. Joining strings but producing wrong output format (spacing, separators) is StringFormat.
```

**Rule 10 — ArrayIndex vs LogicCompareNum**
```
ArrayIndex vs LogicCompareNum — Wrong element retrieved from arr[i] due to wrong index is ArrayIndex. Wrong threshold in a comparison like if(arr[i]>5) is LogicCompareNum.
```

**Rule 11 — ArrayIndex vs For**
```
ArrayIndex vs For — Wrong array element accessed inside a correct loop is ArrayIndex. Wrong loop bounds for array iteration: check if it is the comparison value (LogicCompareNum) or the loop setup (For).
```

**Rule 12 — LogicCompareNum vs LogicBoolean**
```
LogicCompareNum vs LogicBoolean — Comparing two numeric values (age>18) incorrectly is LogicCompareNum. Misusing a boolean value (if(x=true), redundant bool==true) is LogicBoolean.
```

**Rule 13 — LogicCompareNum vs LogicAndNotOr**
```
LogicCompareNum vs LogicAndNotOr — A single comparison that is wrong (< instead of <=) is LogicCompareNum. Multiple comparisons combined with the wrong operator (&& instead of ||) is LogicAndNotOr. If both are wrong, tag both.
```

**Rule 14 — NestedFor vs While**
```
NestedFor vs While — Only tag the construct actually in the code. Nested for-loops wrong = NestedFor. While-loop wrong = While. Never tag a construct the student did not write.
```

**The full JSON array as it appears in the prompt:**

```json
[
  {"rule": "LogicCompareNum vs If/Else — If the student writes day==1||day==2||day==3 instead of day>=1&&day<=5, tag LogicCompareNum. The if-statement structure is correct, the comparison inside it is wrong."},
  {"rule": "LogicBoolean vs If/Else — If the student writes vacation==false instead of !vacation, or uses = instead of ==, tag LogicBoolean. The student misunderstands boolean values, not branching structure."},
  {"rule": "LogicAndNotOr vs If/Else — If the student uses && where || was needed or misses parentheses on grouped conditions, tag LogicAndNotOr. The branching structure is fine, the boolean composition is wrong."},
  {"rule": "LogicCompareNum vs For — Off-by-one in a loop termination condition (< vs <=) is LogicCompareNum. The loop structure is correct, the comparison value is wrong. Tag For only when init, update, or overall structure is broken."},
  {"rule": "Math+-*/ vs For — Wrong arithmetic inside a loop body is Math+-*/. Wrong increment in the for-update (i+=1 when it should be i+=2) is For, because the update is part of loop structure."},
  {"rule": "StringEqual vs LogicCompareNum — String comparison with == or .equals() is StringEqual. Numeric comparison with <, >, == between numbers is LogicCompareNum. Never interchangeable."},
  {"rule": "CharEqual vs StringEqual — charAt() comparisons are CharEqual. Full-string .equals() comparisons are StringEqual."},
  {"rule": "StringIndex vs StringLen — Wrong position in charAt()/substring() is StringIndex. Wrong .length() usage or confusing .length with .length() is StringLen."},
  {"rule": "StringConcat vs StringFormat — Failing to join strings mechanically is StringConcat. Joining strings but producing wrong output format (spacing, separators) is StringFormat."},
  {"rule": "ArrayIndex vs LogicCompareNum — Wrong element retrieved from arr[i] due to wrong index is ArrayIndex. Wrong threshold in a comparison like if(arr[i]>5) is LogicCompareNum."},
  {"rule": "ArrayIndex vs For — Wrong array element accessed inside a correct loop is ArrayIndex. Wrong loop bounds for array iteration: check if it is the comparison value (LogicCompareNum) or the loop setup (For)."},
  {"rule": "LogicCompareNum vs LogicBoolean — Comparing two numeric values (age>18) incorrectly is LogicCompareNum. Misusing a boolean value (if(x=true), redundant bool==true) is LogicBoolean."},
  {"rule": "LogicCompareNum vs LogicAndNotOr — A single comparison that is wrong (< instead of <=) is LogicCompareNum. Multiple comparisons combined with the wrong operator (&& instead of ||) is LogicAndNotOr. If both are wrong, tag both."},
  {"rule": "NestedFor vs While — Only tag the construct actually in the code. Nested for-loops wrong = NestedFor. While-loop wrong = While. Never tag a construct the student did not write."}
]
```

---

## Component 8 — Critical Rules

Four unconditional behavioral rules applied before the model returns a response. Rules 1 and 2 suppress output for degenerate inputs (placeholder code, perfect scores — the pipeline skips calling the model entirely for perfect scores, but the rule handles edge cases where score data is imprecise). Rule 3 enforces the closed-world KC vocabulary. Rule 4 enforces chain-of-thought: reasoning must be written before gaps are listed.

```
CRITICAL RULES:
1. If the code is a trivial placeholder (e.g., just "return true;" or "return 0;") with no real attempt, return empty knowledge_gaps.
2. If the student scored 1.0 (perfect), return empty knowledge_gaps.
3. Only use KC names from the 18 defined above. Do not invent new names.
4. Think through your reasoning BEFORE listing gaps. Write your reasoning first, then decide on tags.
```

---

## Component 9 — Output Format (JSON Schema)

Specifies the exact JSON structure the model must return. The `reasoning` field captures the model's diagnostic trace (one free-text explanation for the whole response, not per-tag). The `knowledge_gaps` field is a flat list of bare KC-tag strings. The instruction "ONLY a JSON object, no other text" enables deterministic fence-stripping and `json.loads` parsing.

```
OUTPUT FORMAT:
Respond with ONLY a JSON object, no other text:
{
  "reasoning": "Brief explanation of what the student did wrong and which KCs are affected, applying the hierarchy (specific before structural).",
  "knowledge_gaps": ["KC1", "KC2"]
}
```

---

## Component 10 — Student Code

The student's raw Java submission, injected verbatim inside a fenced code block at the end of the prompt. No reference solution, compiler output, test results, or other context is provided.

**Template** (`{student_code}` is replaced with the raw submission at call time):

````
STUDENT CODE:
```java
{student_code}
```
````

**Filled-in example** (hypothetical submission for Problem 1 — sum with forbidden range):

````
STUDENT CODE:
```java
public int sumForbidden(int a, int b) {
    int sum = a + b;
    if (sum == 10 || sum == 11 || sum == 12) {
        return 20;
    }
    return sum;
}
```
````

In the filled-in example the student enumerates three cases instead of using a range check — a gap the prompt would diagnose as `LogicCompareNum`.

---

## Source Files

Every piece of prompt text in this document is drawn verbatim from the following files. The `build_v3_prompt()` function with its defaults (`rules_mode="full"`, `kc_mode="per_problem"`) assembles this prompt byte-for-byte. The two ablation flags modify only components 4 and 7.

| File | Contents |
|---|---|
| [`lib/v3_prompt.py`](lib/v3_prompt.py) | `build_v3_prompt()` — full prompt assembly; `DISAMBIGUATION_RULES` — all 14 rules verbatim; `ALL_KCS` — the 18 KC names; `REDUCED_RULE_INDICES` — ablation subset `[0, 1, 2, 12]` |
| [`v3_prompt_spec.md`](v3_prompt_spec.md) | Full specification: inputs, ablation flags, output schema, parse pipeline, and what is *not* in the prompt |
| [`lib/llm_batch_analyzer.py`](lib/llm_batch_analyzer.py) | Gemini API call: `gemini-2.5-flash`, `temperature=0.3`, no other decoding parameters |
| [`lib/experiment_utils.py`](lib/experiment_utils.py) | DeepSeek API call: `deepseek-chat`, `temperature=0.3` (cross-model validation) |
| [`dataset/CodeWorkout/Problem_Prompts/problem_prompts.csv`](dataset/CodeWorkout/Problem_Prompts/problem_prompts.csv) | Q-matrix: `Requirement` column (problem statements) and 18 binary KC columns (required KCs per problem) |
| [`experiments/ablation/exp21_v3_ablation.ipynb`](experiments/ablation/exp21_v3_ablation.ipynb) | Gemini ablation study producing headline results (F1 = 0.839, κ = 0.557) |
| [`experiments/ablation/exp22_deepseek_ablation.ipynb`](experiments/ablation/exp22_deepseek_ablation.ipynb) | DeepSeek cross-model ablation (F1 = 0.825, κ = 0.535) |
