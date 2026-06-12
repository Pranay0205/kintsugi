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

Ablation flags (added for the V3/KCDP ablation study; defaults reproduce the
original V3 prompt byte-for-byte):
- rules_mode: "full" (all 14 disambiguation rules)
            | "reduced" (only the 4 that resolve If/Else over-tagging vs
                         LogicCompareNum / LogicAndNotOr)
            | "none" (drop the DISAMBIGUATION RULES block)
- kc_mode:    "per_problem" (inject the filtered required-KC list for this problem)
            | "full_vocab" (no per-problem shortlist; all 18 KCs are candidates)
Everything else (role, curriculum, KC definitions, tagging hierarchy,
redundancy check / worked examples, forced reasoning, critical rules, output
schema) is identical across every condition.
"""

# The 14 disambiguation rules, in original order. Each entry is the rule text
# placed inside {"rule": "..."} in the prompt's DISAMBIGUATION RULES JSON array.
DISAMBIGUATION_RULES = [
    "LogicCompareNum vs If/Else — If the student writes day==1||day==2||day==3 instead of day>=1&&day<=5, tag LogicCompareNum. The if-statement structure is correct, the comparison inside it is wrong.",
    "LogicBoolean vs If/Else — If the student writes vacation==false instead of !vacation, or uses = instead of ==, tag LogicBoolean. The student misunderstands boolean values, not branching structure.",
    "LogicAndNotOr vs If/Else — If the student uses && where || was needed or misses parentheses on grouped conditions, tag LogicAndNotOr. The branching structure is fine, the boolean composition is wrong.",
    "LogicCompareNum vs For — Off-by-one in a loop termination condition (< vs <=) is LogicCompareNum. The loop structure is correct, the comparison value is wrong. Tag For only when init, update, or overall structure is broken.",
    "Math+-*/ vs For — Wrong arithmetic inside a loop body is Math+-*/. Wrong increment in the for-update (i+=1 when it should be i+=2) is For, because the update is part of loop structure.",
    "StringEqual vs LogicCompareNum — String comparison with == or .equals() is StringEqual. Numeric comparison with <, >, == between numbers is LogicCompareNum. Never interchangeable.",
    "CharEqual vs StringEqual — charAt() comparisons are CharEqual. Full-string .equals() comparisons are StringEqual.",
    "StringIndex vs StringLen — Wrong position in charAt()/substring() is StringIndex. Wrong .length() usage or confusing .length with .length() is StringLen.",
    "StringConcat vs StringFormat — Failing to join strings mechanically is StringConcat. Joining strings but producing wrong output format (spacing, separators) is StringFormat.",
    "ArrayIndex vs LogicCompareNum — Wrong element retrieved from arr[i] due to wrong index is ArrayIndex. Wrong threshold in a comparison like if(arr[i]>5) is LogicCompareNum.",
    "ArrayIndex vs For — Wrong array element accessed inside a correct loop is ArrayIndex. Wrong loop bounds for array iteration: check if it is the comparison value (LogicCompareNum) or the loop setup (For).",
    "LogicCompareNum vs LogicBoolean — Comparing two numeric values (age>18) incorrectly is LogicCompareNum. Misusing a boolean value (if(x=true), redundant bool==true) is LogicBoolean.",
    "LogicCompareNum vs LogicAndNotOr — A single comparison that is wrong (< instead of <=) is LogicCompareNum. Multiple comparisons combined with the wrong operator (&& instead of ||) is LogicAndNotOr. If both are wrong, tag both.",
    "NestedFor vs While — Only tag the construct actually in the code. Nested for-loops wrong = NestedFor. While-loop wrong = While. Never tag a construct the student did not write.",
]

# Indices of the 4 rules kept in the "reduced" condition: the three structural
# If/Else disambiguators plus the inter-Logic compound-condition rule.
REDUCED_RULE_INDICES = [0, 1, 2, 12]

# All 18 KC names, in the same order as the KC DEFINITIONS block below.
ALL_KCS = [
    "If/Else", "NestedIf", "While", "For", "NestedFor",
    "Math+-*/", "Math%", "LogicAndNotOr", "LogicCompareNum", "LogicBoolean",
    "StringFormat", "StringConcat", "StringIndex", "StringLen",
    "StringEqual", "CharEqual", "ArrayIndex", "DefFunction",
]


def _build_kc_injection_block(required_kcs, kc_mode):
    """Build the per-problem KC injection section (component 4)."""
    if kc_mode == "per_problem":
        required_kcs_str = ", ".join(required_kcs)
        return (
            f"REQUIRED KCs FOR THIS PROBLEM: [{required_kcs_str}]\n"
            "These are the KCs this problem is designed to test. Check these first. "
            "However, if the student's code reveals gaps in other KCs not on this list, tag those too."
        )
    if kc_mode == "full_vocab":
        all_kcs_str = ", ".join(ALL_KCS)
        return (
            f"AVAILABLE KCs: [{all_kcs_str}]\n"
            "Any of these 18 KCs may apply to this problem. There is no per-problem shortlist — "
            "decide purely from the student's code which KCs reveal gaps."
        )
    raise ValueError(f"Unknown kc_mode: {kc_mode!r} (expected 'per_problem' or 'full_vocab')")


def _build_disambiguation_block(rules_mode):
    """Build the DISAMBIGUATION RULES section (component 6), with trailing blank line.

    Returns "" for rules_mode='none' so the section disappears cleanly.
    """
    if rules_mode == "none":
        return ""
    if rules_mode == "full":
        rules = DISAMBIGUATION_RULES
    elif rules_mode == "reduced":
        rules = [DISAMBIGUATION_RULES[i] for i in REDUCED_RULE_INDICES]
    else:
        raise ValueError(f"Unknown rules_mode: {rules_mode!r} (expected 'full', 'reduced', or 'none')")

    rules_json = "[\n" + ",\n".join(f'  {{"rule": "{r}"}}' for r in rules) + "\n]"
    return (
        "DISAMBIGUATION RULES:\n"
        "When two KCs seem applicable, use these rules to pick the correct one.\n"
        "\n"
        f"{rules_json}\n"
        "\n"
    )


def build_v3_prompt(problem_id, requirement, assignment_id, required_kcs, student_code, score,
                    rules_mode="full", kc_mode="per_problem"):
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
    rules_mode : "full" | "reduced" | "none" - disambiguation-rule ablation
    kc_mode : "per_problem" | "full_vocab" - per-problem KC injection ablation
    """

    kc_injection_block = _build_kc_injection_block(required_kcs, kc_mode)
    disambiguation_block = _build_disambiguation_block(rules_mode)

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

{kc_injection_block}

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

{disambiguation_block}CRITICAL RULES:
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
