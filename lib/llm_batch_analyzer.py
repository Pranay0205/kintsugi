import json
from typing import Hashable
from google import genai
from google.genai import types
from utils.constants import GEMINI_API_KEY
from utils.dataset import load_topics_json, load_problem_descriptions, load_joined_datasets, get_best_attempts


client = genai.Client(api_key=GEMINI_API_KEY)

# Load curriculum and problems
topics = load_topics_json()
problems = load_problem_descriptions()

# Problems to focus on (keep token size low)
FOCUS_PROBLEMS = [32, 33, 34]  # Adjust based on your data


def create_system_instruction() -> str:
    """
    Create system instruction with curriculum embedded.
    Focuses on individual student gaps + future predictions.
    """

    # Filter problems to only focused ones
    focused_problems = {k: v for k,
                        v in problems.items() if int(k) in FOCUS_PROBLEMS}

    return f"""You are an expert CS1 instructor analyzing individual student code submissions to identify knowledge gaps and predict future struggles.

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
// Student code for finding substring
for(int i = 0; i < str.length(); i++) {{
    if(str.substring(i, i+5).equals("bread")) // crashes at end
```
Gap: "Off-by-one error in loop bounds - doesn't account for substring length"
Missing concept: Loop termination conditions with string operations
Future risk: Will struggle with array traversal, nested loops, any boundary-sensitive algorithms

Example 2 - String method confusion:
```java
// Student used length instead of length()
int len = str.length;  // wrong
```
Gap: "Confuses String.length() method with array.length property"
Missing concept: Difference between methods and properties in Java
Future risk: Will make similar errors with other String methods, ArrayList.size() vs array.length

Example 3 - Logic flow issue:
```java
// Returns inside loop, misses multiple occurrences
for(int i = 0; i < str.length(); i++) {{
    if(str.charAt(i) == 'x') return true;
    else return false;  // returns on first char!
}}
```
Gap: "Premature return in loop - doesn't understand loop continuation"
Missing concept: Control flow in loops, when to return vs continue
Future risk: Will fail problems requiring full iteration (counting, finding all matches)

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

OUTPUT FORMAT:
Return ONLY valid JSON:
{{
  "student_analysis": [
    {{
      "student_id": "SubjectID",
      "problem_id": "ProblemID",
      "score": 0.0,
      "knowledge_gaps": [
        {{
          "gap": "Specific description of what student doesn't understand",
          "evidence": "Code snippet or behavior that shows this gap",
          "missing_concept": "The underlying concept they're missing",
          "severity": "critical/moderate/minor"
        }}
      ],
      "future_predictions": [
        {{
          "at_risk_topic": "Topic they will struggle with",
          "reason": "Why this gap will cause problems there",
          "prerequisite_gap": "What they need to learn first"
        }}
      ],
      "recommended_intervention": "Specific teaching suggestion for this student"
    }}
  ],
  "class_summary": {{
    "common_gaps": ["List of gaps affecting multiple students"],
    "highest_risk_students": ["Student IDs needing immediate attention"],
    "suggested_review_topics": ["Topics instructor should revisit"]
  }}
}}
"""


def get_focused_best_attempts(problem_ids: list[int] = FOCUS_PROBLEMS) -> list[dict]:
    """
    Load data, get best attempts, filter to focused problems.
    Returns list of submission dicts ready for analysis.
    """
    df = load_joined_datasets()

    if df is None:
        return []

    # Get best attempts
    best_df = get_best_attempts(df)

    # Filter to focused problems
    focused_df = best_df[best_df['ProblemID'].isin(problem_ids)]

    print(f"Focused submissions: {len(focused_df)} rows")
    print(f"  Problems: {focused_df['ProblemID'].unique().tolist()}")
    print(f"  Students: {focused_df['SubjectID'].nunique()}")

    # Convert to list of dicts
    submissions = focused_df.to_dict('records')

    return submissions


def analyze_student_submissions(submissions: list[dict], limit: int = 30) -> dict | None:
    """
    Analyze student submissions with focus on individual gaps and predictions.

    Args:
        submissions: List of submission dicts (best attempts only)
        limit: Max submissions to analyze (token management)
    """

    # Limit submissions
    submissions = submissions[:limit]

    if not submissions:
        print("No submissions to analyze.")
        return None

    formatted_input = format_submissions(submissions)
    system_instruction = create_system_instruction()

    print(f"Analyzing {len(submissions)} submissions...")
    print(
        f"Estimated tokens: ~{len(formatted_input.split()) + len(system_instruction.split())} words")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=formatted_input,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3,
            response_mime_type="application/json"
        )
    )

    if response.text:
        result = clean_json_response(response.text)
        try:
            return json.loads(result)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Raw response: {response.text[:500]}...")
            return None
    return None


def format_submissions(submissions: list[dict]) -> str:
    """Format submissions for analysis."""

    formatted = "STUDENT SUBMISSIONS TO ANALYZE:\n\n"

    for idx, sub in enumerate(submissions, 1):
        code = sub.get('Code', 'NO CODE')
        student_id = sub.get('SubjectID', 'unknown')
        problem_id = sub.get('ProblemID', 'unknown')
        score = sub.get('Score', 0)
        attempt = sub.get('Attempt', 'unknown')

        # Include compile result if available
        compile_result = sub.get('Compile.Result', '')

        formatted += f"""--- Submission {idx} ---
Student ID: {student_id}
Problem ID: {problem_id}
Score: {float(score) * 100:.1f}%
Attempt #: {attempt}
Compiled: {compile_result if compile_result else 'Unknown'}

Code:
```java
{code}
```

"""

    formatted += "\nAnalyze each student's knowledge state and predict future struggles."

    return formatted


def clean_json_response(text: str) -> str:
    """Clean JSON response from markdown formatting."""
    result = text.strip()
    if result.startswith("```json"):
        result = result[7:]
    if result.startswith("```"):
        result = result[3:]
    if result.endswith("```"):
        result = result[:-3]
    return result.strip()


def print_student_analysis(results: dict) -> None:
    """Print individual student analysis results."""

    if not results:
        print("No results to display.")
        return

    print("\n" + "=" * 70)
    print("📊 INDIVIDUAL STUDENT ANALYSIS")
    print("=" * 70)

    # Individual students
    for student in results.get("student_analysis", []):
        student_id = student.get("student_id", "Unknown")
        problem_id = student.get("problem_id", "Unknown")
        score = student.get("score", 0)

        print(
            f"\n👤 Student {student_id} | Problem {problem_id} | Score: {score}%")
        print("-" * 50)

        # Knowledge gaps
        gaps = student.get("knowledge_gaps", [])
        if gaps:
            print("  🔴 KNOWLEDGE GAPS:")
            for gap in gaps:
                severity = gap.get("severity", "unknown")
                severity_icon = {"critical": "🚨", "moderate": "⚠️", "minor": "📝"}.get(
                    severity, "•")
                print(f"     {severity_icon} {gap.get('gap', 'N/A')}")
                print(
                    f"        Evidence: {gap.get('evidence', 'N/A')[:80]}...")
                print(f"        Missing: {gap.get('missing_concept', 'N/A')}")

        # Future predictions
        predictions = student.get("future_predictions", [])
        if predictions:
            print("  🔮 FUTURE RISK:")
            for pred in predictions:
                print(
                    f"     • Will struggle with: {pred.get('at_risk_topic', 'N/A')}")
                print(f"       Reason: {pred.get('reason', 'N/A')}")

        # Intervention
        intervention = student.get("recommended_intervention", "")
        if intervention:
            print(f"  💡 RECOMMENDATION: {intervention}")

    # Class summary
    summary = results.get("class_summary", {})
    if summary:
        print("\n" + "=" * 70)
        print("📋 CLASS SUMMARY")
        print("=" * 70)

        common = summary.get("common_gaps", [])
        if common:
            print("\n  Common Gaps Across Students:")
            for gap in common:
                print(f"    • {gap}")

        at_risk = summary.get("highest_risk_students", [])
        if at_risk:
            print(
                f"\n  🚨 Students Needing Attention: {', '.join(map(str, at_risk))}")

        review = summary.get("suggested_review_topics", [])
        if review:
            print("\n  📚 Suggested Topics to Review:")
            for topic in review:
                print(f"    • {topic}")

    print("\n" + "=" * 70)


# Main execution function
def run_analysis(problem_ids: list[int] = FOCUS_PROBLEMS, max_students: int = 30):
    """
    Run the full analysis pipeline.

    Args:
        problem_ids: List of problem IDs to focus on
        max_students: Maximum number of students to analyze
    """
    print(f"Starting analysis for problems: {problem_ids}")
    print(f"Max students: {max_students}")

    # Get focused best attempts
    submissions = get_focused_best_attempts(problem_ids)

    if not submissions:
        print("No submissions found.")
        return None

    # Analyze
    results = analyze_student_submissions(submissions, limit=max_students)

    if not results:
        print("No results were present")
        return []
    # Print results
    print_student_analysis(results)

    return results


if __name__ == "__main__":
    # Run with default settings
    results = run_analysis(
        problem_ids=[32, 33, 34],  # Adjust to your problems
        max_students=20
    )
