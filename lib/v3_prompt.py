"""
V3 Prompt Template for KC Gap Detection
========================================
Assembled at runtime by build_v3_prompt(problem_id, requirement, required_kcs, student_code)

Components:
1. Role declaration (text)
2. Problem context (JSON)
3. KC definitions - all 18 (JSON)
4. Required KCs for this problem (text)
5. Tagging hierarchy (text)
6. Disambiguation rules - all 14 (JSON)
7. Critical rules (text)
8. Output format (JSON example)
9. Student code (raw code)
"""


def build_v3_prompt(problem_id, requirement, assignment_id, required_kcs, student_code, score):
    """
    Build the V3 curriculum-aware prompt.

    Parameters
    ----------
    problem_id : int
    requirement : str - the problem description shown to the student
    assignment_id : int - maps to chapter/difficulty
    required_kcs : list[str] - KCs this problem is designed to test (from problem_prompts.csv)
    student_code : str - the student's submitted code
    score : float - the student's score (0.0 to 1.0)
    """

    required_kcs_str = ", ".join(required_kcs)

    prompt = f"""You are an expert CS1 instructor analyzing a single student Java code submission to identify knowledge gaps.

PROBLEM CONTEXT:
{{
  "problem_id": {problem_id},
  "assignment_id": {assignment_id},
  "requirement": "{requirement}",
  "student_score": {score}
}}

KC DEFINITIONS:
Below are all 18 Knowledge Components (KCs) used in this course. Each includes what a gap looks like in student code.

{{
  "If/Else": {{
    "category": "Control Flow",
    "type": "structural",
    "gap_signal": "Tag when the STRUCTURE is wrong: missing branches that the problem requires, wrong order of tests, a case that is never handled, two sequential ifs where if/else was needed. Do NOT tag for missing else when a simple if-with-early-return is cleaner. Do NOT tag when the condition inside the if is wrong but the branching structure is correct — that belongs to a Logic KC."
  }},
  "NestedIf": {{
    "category": "Control Flow",
    "type": "structural",
    "gap_signal": "Tag only if the code actually contains nested ifs and uses them incorrectly (wrong nesting order, conditions at wrong level). Do NOT tag 'they should have nested' — only tag what the student actually wrote."
  }},
  "While": {{
    "category": "Loops",
    "type": "structural",
    "gap_signal": "Tag when the loop structure itself is wrong: wrong stopping condition, never updates the loop variable, infinite loop. Do NOT tag if the problem does not require a while loop and the student did not use one. Do NOT tag if the loop structure is fine but the logic inside it is wrong."
  }},
  "For": {{
    "category": "Loops",
    "type": "structural",
    "gap_signal": "Tag when the loop structure is wrong: wrong initialization, wrong update expression, loop variable does not iterate correctly. Off-by-one in the termination condition belongs to LogicCompareNum, not For."
  }},
  "NestedFor": {{
    "category": "Loops",
    "type": "structural",
    "gap_signal": "Tag only if code contains nested loops and uses them incorrectly (wrong inner bounds, reusing outer variable, wrong nesting order). Do NOT tag if the problem does not require nested loops. Do NOT infer 'the student would struggle with nested loops' — only tag what is actually in the code."
  }},
  "Math+-*/": {{
    "category": "Math",
    "type": "specific",
    "gap_signal": "Tag when the student uses the wrong arithmetic operation or gets arithmetic logic wrong: dividing when they should multiply, missing integer-division truncation, wrong order of operations."
  }},
  "Math%": {{
    "category": "Math",
    "type": "specific",
    "gap_signal": "Tag when the student needs modulo and does not use it, or uses it wrong: checking divisibility with / instead of %, wrong modulo base, misunderstanding what % returns."
  }},
  "LogicAndNotOr": {{
    "category": "Logic",
    "type": "specific",
    "gap_signal": "Tag when the student combines booleans wrong: uses && where || was needed, inverts a condition incorrectly with !, misses a case when chaining compound conditions, wrong short-circuit logic."
  }},
  "LogicCompareNum": {{
    "category": "Logic",
    "type": "specific",
    "gap_signal": "Tag for any numeric comparison bug: wrong direction (< vs >), off-by-one at boundary (< vs <=), enumerating values (day==1||day==2||day==3) instead of using ranges (day>=1 && day<=5), comparing when equality was needed or vice versa."
  }},
  "LogicBoolean": {{
    "category": "Logic",
    "type": "specific",
    "gap_signal": "Tag for: if (x = true) (assignment instead of comparison), returning true/false in the wrong branch, unnecessary if (bool == true) revealing misunderstanding of boolean type, using 0/1 instead of true/false."
  }},
  "StringFormat": {{
    "category": "Strings",
    "type": "specific",
    "gap_signal": "Tag when the student cannot produce the expected output format even when their logic is close: wrong spacing, missing separators, wrong order of concatenated pieces in the final output string."
  }},
  "StringConcat": {{
    "category": "Strings",
    "type": "specific",
    "gap_signal": "Tag when concatenation is missing, in wrong order, or produces wrong result. Not about output format (that is StringFormat) — about the mechanical act of joining strings."
  }},
  "StringIndex": {{
    "category": "Strings",
    "type": "specific",
    "gap_signal": "Tag for wrong index, index out of bounds, off-by-one in string position, using wrong substring bounds."
  }},
  "StringLen": {{
    "category": "Strings",
    "type": "specific",
    "gap_signal": "Tag when the student confuses .length() method with .length property (Java arrays), or uses wrong length value for substring bounds, or does not account for zero-based indexing with length."
  }},
  "StringEqual": {{
    "category": "Strings",
    "type": "specific",
    "gap_signal": "Tag when the student uses == on strings instead of .equals(), or compares the wrong parts of strings. Do NOT tag for numeric comparisons — that is LogicCompareNum."
  }},
  "CharEqual": {{
    "category": "Strings",
    "type": "specific",
    "gap_signal": "Tag when comparison at the character level is wrong: comparing wrong char position, wrong char literal, confusing char with String type."
  }},
  "ArrayIndex": {{
    "category": "Arrays",
    "type": "specific",
    "gap_signal": "Tag for out-of-bounds access, off-by-one in array indexing, wrong index variable, confusing index with value stored at that index."
  }},
  "DefFunction": {{
    "category": "Functions",
    "type": "specific",
    "gap_signal": "Tag when the problem asks for a specific helper method and the student's helper is missing, incomplete, has wrong signature, or has broken logic inside it."
  }}
}}

REQUIRED KCs FOR THIS PROBLEM: [{required_kcs_str}]
These are the KCs this problem is designed to test. Check these first. However, if the student's code reveals gaps in other KCs not on this list, tag those too.

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

DISAMBIGUATION RULES:
When two KCs seem applicable, use these rules to pick the correct one.

[
  {{"rule": "LogicCompareNum vs If/Else — If the student writes day==1||day==2||day==3 instead of day>=1&&day<=5, tag LogicCompareNum. The if-statement structure is correct, the comparison inside it is wrong."}},
  {{"rule": "LogicBoolean vs If/Else — If the student writes vacation==false instead of !vacation, or uses = instead of ==, tag LogicBoolean. The student misunderstands boolean values, not branching structure."}},
  {{"rule": "LogicAndNotOr vs If/Else — If the student uses && where || was needed or misses parentheses on grouped conditions, tag LogicAndNotOr. The branching structure is fine, the boolean composition is wrong."}},
  {{"rule": "LogicCompareNum vs For — Off-by-one in a loop termination condition (< vs <=) is LogicCompareNum. The loop structure is correct, the comparison value is wrong. Tag For only when init, update, or overall structure is broken."}},
  {{"rule": "Math+-*/ vs For — Wrong arithmetic inside a loop body is Math+-*/. Wrong increment in the for-update (i+=1 when it should be i+=2) is For, because the update is part of loop structure."}},
  {{"rule": "StringEqual vs LogicCompareNum — String comparison with == or .equals() is StringEqual. Numeric comparison with <, >, == between numbers is LogicCompareNum. Never interchangeable."}},
  {{"rule": "CharEqual vs StringEqual — charAt() comparisons are CharEqual. Full-string .equals() comparisons are StringEqual."}},
  {{"rule": "StringIndex vs StringLen — Wrong position in charAt()/substring() is StringIndex. Wrong .length() usage or confusing .length with .length() is StringLen."}},
  {{"rule": "StringConcat vs StringFormat — Failing to join strings mechanically is StringConcat. Joining strings but producing wrong output format (spacing, separators) is StringFormat."}},
  {{"rule": "ArrayIndex vs LogicCompareNum — Wrong element retrieved from arr[i] due to wrong index is ArrayIndex. Wrong threshold in a comparison like if(arr[i]>5) is LogicCompareNum."}},
  {{"rule": "ArrayIndex vs For — Wrong array element accessed inside a correct loop is ArrayIndex. Wrong loop bounds for array iteration: check if it is the comparison value (LogicCompareNum) or the loop setup (For)."}},
  {{"rule": "LogicCompareNum vs LogicBoolean — Comparing two numeric values (age>18) incorrectly is LogicCompareNum. Misusing a boolean value (if(x=true), redundant bool==true) is LogicBoolean."}},
  {{"rule": "LogicCompareNum vs LogicAndNotOr — A single comparison that is wrong (< instead of <=) is LogicCompareNum. Multiple comparisons combined with the wrong operator (&& instead of ||) is LogicAndNotOr. If both are wrong, tag both."}},
  {{"rule": "NestedFor vs While — Only tag the construct actually in the code. Nested for-loops wrong = NestedFor. While-loop wrong = While. Never tag a construct the student did not write."}}
]

CRITICAL RULES:
1. If the code is a trivial placeholder (e.g., just "return true;" or "return 0;") with no real attempt, return empty knowledge_gaps.
2. If the student scored 1.0 (perfect), return empty knowledge_gaps.
3. Only use KC names from the 18 defined above. Do not invent new names.
4. Think through your reasoning BEFORE listing gaps. Write your reasoning first, then decide on tags.

OUTPUT FORMAT:
Respond with ONLY a JSON object, no other text:
{{
  "reasoning": "Brief explanation of what the student did wrong and which KCs are affected, applying the hierarchy (specific before structural).",
  "knowledge_gaps": ["KC1", "KC2"]
}}

STUDENT CODE:
```java
{student_code}
```"""

    return prompt
