"""
Prompt strategies for LLM-based knowledge gap detection.

Defines four prompt engineering approaches compared in the thesis:
1. Zero-Shot - Direct instruction, no examples
2. Few-Shot - Instruction with annotated examples
3. Chain-of-Thought - Step-by-step reasoning chain
4. Curriculum-Aware - Role-based + curriculum context + strict KC tags

"""

import json
from typing import Callable


# ---------------------------------------------------------------------------
# KC Vocabulary (single source of truth - matches problem_prompts.csv columns)
# ---------------------------------------------------------------------------

KC_TAGS = [
    "If/Else",
    "NestedIf",
    "While",
    "For",
    "NestedFor",
    "Math+-*/",
    "Math%",
    "LogicAndNotOr",
    "LogicCompareNum",
    "LogicBoolean",
    "StringFormat",
    "StringConcat",
    "StringIndex",
    "StringLen",
    "StringEqual",
    "CharEqual",
    "ArrayIndex",
    "DefFunction",
]


# ---------------------------------------------------------------------------
# 1. Zero-Shot
# ---------------------------------------------------------------------------

def get_zero_shot_prompt() -> str:
    """Direct instruction without examples."""
    return """You are a Computer Science instructor.
Analyze the provided student Java code submission.
Identify specific knowledge gaps explaining why the code is incorrect or inefficient.
Predict any future topics the student might struggle with based on these gaps.

If the student's code is correct and demonstrates solid understanding, return empty lists for both keys.

Return the result in JSON format with keys: 'knowledge_gaps' (list of strings) and 'future_predictions' (list of strings).
"""


# ---------------------------------------------------------------------------
# 2. Few-Shot
# ---------------------------------------------------------------------------

def get_few_shot_prompt() -> str:
    """Instruction with two annotated examples."""
    return """You are a CS instructor analyzing student code. Identify knowledge gaps and predict future struggles.

Example 1:
Code:
for(int i=0; i<=str.length(); i++) {
   char c = str.charAt(i);
}
Analysis:
{
  "knowledge_gaps": ["Off-by-one error (<= length instead of < length) causes IndexOutOfBoundsException"],
  "future_predictions": ["Array traversal", "Nested loops"]
}

Example 2:
Code:
if (str == "hello") { return true; }
Analysis:
{
  "knowledge_gaps": ["String comparison using == instead of .equals()"],
  "future_predictions": ["Object references vs primitives", "Memory model"]
}

If the student's code is correct and demonstrates solid understanding, return empty lists for both keys.

Now analyze the user's submission and provide output in the same JSON format.
"""


# ---------------------------------------------------------------------------
# 3. Chain-of-Thought
# ---------------------------------------------------------------------------

def get_chain_of_thought_prompt() -> str:
    """Forces step-by-step reasoning before concluding."""
    return """You are an expert CS1 instructor. Analyze the student's Java code submission step-by-step.

Follow this reasoning chain EXACTLY before producing your final answer:

STEP 1 - WHAT DOES THE CODE DO?
Read the code carefully. Describe what the student's code actually does, line by line.

STEP 2 - WHERE DOES IT FAIL?
Compare the code's behavior to the problem requirements (inferred from the method signature and context).
Identify the specific lines or logic that cause incorrect output or errors.

STEP 3 - WHAT CONCEPT IS MISSING?
For each failure point, determine the underlying CS concept the student does not understand.
Distinguish between:
- True conceptual gaps (student misunderstands a concept)
- Simple typos or syntax slips (ignore these)

STEP 4 - PREDICT FUTURE IMPACT
Based on the missing concepts, predict which future topics will be difficult.
Only predict topics that are logical downstream consequences of the identified gaps.

After completing all 4 steps, produce your final answer as JSON:
{
  "reasoning_chain": {
    "step1_behavior": "What the code actually does...",
    "step2_failures": "Where and why it fails...",
    "step3_missing_concepts": "What concepts are missing...",
    "step4_future_impact": "What future topics are at risk..."
  },
  "knowledge_gaps": ["gap1", "gap2"],
  "future_predictions": ["topic1", "topic2"]
}

If the student's code is correct and demonstrates solid understanding, return empty lists for knowledge_gaps and future_predictions.

IMPORTANT: Complete all reasoning steps BEFORE writing the final gaps and predictions.
"""


# ---------------------------------------------------------------------------
# 4. Curriculum-Aware (Hybrid)
# ---------------------------------------------------------------------------

def build_curriculum_aware_prompt(
    topics: dict,
    problems: dict,
    focus_problem_ids: list,
) -> str:
    """
    Build the full curriculum-aware system instruction.

    Parameters
    ----------
    topics : dict
        Course curriculum structure (from java_topics.json).
    problems : dict
        Mapping of problem_id -> problem description text.
    focus_problem_ids : list[int]
        Which problems to include in the prompt context.
    """
    focused_problems = {
        k: v for k, v in problems.items() if int(k) in focus_problem_ids
    }

    base = f"""You are an expert CS1 instructor analyzing individual student code submissions to identify knowledge gaps and predict future struggles.

COURSE CURRICULUM:
{json.dumps(topics, indent=2)}

PROBLEM DESCRIPTIONS:
{json.dumps(focused_problems, indent=2)}

YOUR TASK:
For each student, analyze their code submission and:
1. Identify specific knowledge gaps based on errors in their code
2. Predict which future topics/problems they may struggle with based on current gaps

ANALYSIS APPROACH:
1. Look at what the student attempted vs. what was required
2. Identify misconceptions (not just syntax errors)
3. Determine prerequisite concepts the student is missing
4. Predict downstream impact on future learning

EXAMPLES OF GOOD GAP IDENTIFICATION:

Example 1 - Loop boundary error:
```java
for(int i = 0; i < str.length(); i++) {{{{
    if(str.substring(i, i+5).equals("bread")) // crashes at end
```
Gap: "Off-by-one error in loop bounds - doesn't account for substring length"
Missing concept: For
Future risk: NestedFor, ArrayIndex

Example 2 - String method confusion:
```java
int len = str.length;  // wrong
```
Gap: "Confuses String.length() method with array.length property"
Missing concept: StringLen
Future risk: StringIndex, ArrayIndex

Example 3 - Logic flow issue:
```java
for(int i = 0; i < str.length(); i++) {{{{
    if(str.charAt(i) == 'x') return true;
    else return false;  // returns on first char!
}}}}
```
Gap: "Premature return in loop - doesn't understand loop continuation"
Missing concept: For, LogicBoolean
Future risk: NestedFor, LogicAndNotOr

WHAT TO LOOK FOR:
- Syntax errors that reveal conceptual confusion (not typos)
- Logic errors showing misunderstanding of problem requirements
- Missing edge case handling (empty strings, boundaries)
- Incorrect use of built-in methods
- Control flow issues (early returns, infinite loops)

WHAT TO IGNORE:
- Simple typos (missing semicolon student would catch)
- Style/formatting issues
- Variable naming choices
- Code that works but is inefficient

IMPORTANT RULES:

1. For students with Score >= 90%:
   - Only report CRITICAL conceptual gaps that could cause problems later
   - Do NOT report efficiency issues (StringBuilder vs +, charAt vs substring)

2. For students with Score < 90%:
   - Focus on WHY their code fails test cases
   - Identify the conceptual misunderstanding causing failures

3. A "knowledge gap" means the student DOES NOT UNDERSTAND a concept,
   NOT that they used a less efficient approach.

4. If the student's code is correct and demonstrates solid understanding,
   return empty knowledge_gaps and future_predictions lists.
   
5. If student has just return statements with no logic, simply return no gaps instead of trying to infer a gap from lack of content. You can't identify a specific misconception if they haven't attempted any logic. [HIGLY CRITICAL: Do NOT fabricate gaps based on missing code. Only identify gaps from actual errors in their code.]
      

OUTPUT FORMAT:
Return ONLY valid JSON:
{{{{
  "student_analysis": [
    {{{{
      "student_id": "SubjectID",
      "problem_id": "ProblemID",
      "score": 0.0,
      "knowledge_gaps": [
        {{{{
          "gap": "Specific description",
          "evidence": "Code snippet showing this gap",
          "missing_concept": "STRICT_KC_TAG",
          "severity": "critical/moderate/minor"
        }}}}
      ],
      "future_predictions": [
        {{{{
          "at_risk_topic": "STRICT_KC_TAG",
          "reason": "Why this gap causes problems there",
          "prerequisite_gap": "What they need to learn first"
        }}}}
      ],
      "recommended_intervention": "Teaching suggestion"
    }}}}
  ],
  "class_summary": {{{{
    "common_gaps": ["Gaps affecting multiple students"],
    "highest_risk_students": ["Student IDs needing attention"],
    "suggested_review_topics": ["Topics to revisit"]
  }}}}
}}}}
"""

    # ------------------------------------------------------------------
    # Use exact KC names from problem_prompts.csv instead of
    # generic tags. This ensures WeakSkillOverlap can match LLM output
    # against the student mental model which uses the same KC vocabulary.
    #
    # OLD (broken): Loop, NestedLoop, String, Array, Logic, Condition,
    #               Method, Math, Indexing, Comparison
    # NEW (fixed):  If/Else, NestedIf, While, For, NestedFor, Math+-*/,
    #               Math%, LogicAndNotOr, LogicCompareNum, LogicBoolean,
    #               StringFormat, StringConcat, StringIndex, StringLen,
    #               StringEqual, CharEqual, ArrayIndex, DefFunction
    # ------------------------------------------------------------------

    strict_tags = """

STRICT OUTPUT RULES:
Separate quantitative tags from qualitative descriptions.

1. 'knowledge_gaps' must be a list of objects with 'missing_concept' using a STRICT KC TAG:
   { "gap": "description", "evidence": "code", "missing_concept": "STRICT_KC_TAG", "severity": "level" }

2. 'future_predictions' must be a list of objects with 'at_risk_topic' using a STRICT KC TAG:
   { "at_risk_topic": "STRICT_KC_TAG", "reason": "explanation", "prerequisite_gap": "description" }

PERMITTED KC TAGS - use ONLY these exact names for 'missing_concept' and 'at_risk_topic':

Conditional Skills:
- If/Else
- NestedIf

Loop Skills:
- While
- For
- NestedFor

Math Skills:
- Math+-*/
- Math%

Logic Skills:
- LogicAndNotOr
- LogicCompareNum
- LogicBoolean

String Skills:
- StringFormat
- StringConcat
- StringIndex
- StringLen
- StringEqual
- CharEqual

Array Skills:
- ArrayIndex

Function Skills:
- DefFunction

CRITICAL RULES FOR TAGS:
- Do NOT use generic terms like "Logic", "Loop", "String", "Condition", "Method", "Array".
- ALWAYS use the SPECIFIC KC tag from the list above (e.g., "For" not "Loop", "If/Else" not "Condition").
- If a gap spans multiple skills, list each relevant specific KC tag as a SEPARATE future_prediction entry.
- If no KC tag fits exactly, use the closest match from the list above.
"""

    return base + strict_tags


# ---------------------------------------------------------------------------
# Overlap Calculation
# ---------------------------------------------------------------------------

def calculate_weak_skill_overlap(
    llm_output: dict,
    weak_skills: list,
) -> dict:
    """
    Calculate overlap between LLM-predicted at-risk topics and the student's
    actual weak skills from their mental model.

    Now works correctly because both sides use the same KC vocabulary
    from problem_prompts.csv.

    Parameters
    ----------
    llm_output : dict
        Parsed JSON output from the LLM (Curriculum-Aware strategy).
    weak_skills : list[str]
        Student's weak skills from get_weak_skills(),
        e.g. ["LogicCompareNum", "NestedIf"].

    Returns
    -------
    dict with:
        - overlap_count: int - number of LLM predictions matching weak skills
        - overlap_skills: list[str] - which specific KCs overlapped
        - total_predictions: int - total at_risk_topics the LLM predicted
        - total_weak_skills: int - total weak skills in mental model
        - overlap_ratio: float - overlap_count / total_predictions (precision)
        - coverage_ratio: float - overlap_count / total_weak_skills (recall)
    """
    weak_set = set(weak_skills)

    # Extract at_risk_topic tags from LLM output
    predicted_tags = set()
    try:
        analyses = llm_output.get("student_analysis", [])
        for analysis in analyses:
            for pred in analysis.get("future_predictions", []):
                tag = pred.get("at_risk_topic", "")
                if tag:
                    predicted_tags.add(tag)
    except (AttributeError, TypeError):
        pass

    # Also extract missing_concept from knowledge_gaps
    concept_tags = set()
    try:
        analyses = llm_output.get("student_analysis", [])
        for analysis in analyses:
            for gap in analysis.get("knowledge_gaps", []):
                concept = gap.get("missing_concept", "")
                if concept in KC_TAGS:
                    concept_tags.add(concept)
    except (AttributeError, TypeError):
        pass

    all_llm_tags = predicted_tags | concept_tags
    overlap = all_llm_tags & weak_set

    total_preds = len(all_llm_tags)
    total_weak = len(weak_set)

    return {
        "overlap_count": len(overlap),
        "overlap_skills": sorted(overlap),
        "total_predictions": total_preds,
        "total_weak_skills": total_weak,
        "overlap_ratio": (
            len(overlap) / total_preds if total_preds > 0 else 0.0
        ),
        "coverage_ratio": (
            len(overlap) / total_weak if total_weak > 0 else 0.0
        ),
        "llm_tags": sorted(all_llm_tags),
        "weak_skills": sorted(weak_set),
    }


# ---------------------------------------------------------------------------
# Strategy Registry
# ---------------------------------------------------------------------------

SIMPLE_STRATEGIES: dict[str, Callable] = {
    "Zero-Shot": get_zero_shot_prompt,
    "Few-Shot": get_few_shot_prompt,
    "Chain-of-Thought": get_chain_of_thought_prompt,
}
