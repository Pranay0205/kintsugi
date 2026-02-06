"""LLM-based student submission analyzer using Gemini.

Provides functions for:
- Formatting student submissions for LLM input
- Sending analysis requests to Gemini
- Parsing and cleaning JSON responses
- Orchestrating end-to-end analysis pipelines
"""

import json

from google import genai
from google.genai import types

from lib.prompts import build_curriculum_aware_prompt
from utils.constants import GEMINI_API_KEY, FOCUS_PROBLEMS
from utils.dataset import (
    get_best_attempts,
    load_joined_datasets,
    load_problem_descriptions,
    load_topics_json,
)

client = genai.Client(api_key=GEMINI_API_KEY)


# ---------------------------------------------------------------------------
# Formatting & parsing helpers
# ---------------------------------------------------------------------------


def format_submissions(submissions: list[dict]) -> str:
    """Format a list of submission dicts into a single LLM user-message."""
    parts = ["STUDENT SUBMISSIONS TO ANALYZE:\n"]

    for idx, sub in enumerate(submissions, 1):
        code = sub.get("Code", "NO CODE")
        student_id = sub.get("SubjectID", "unknown")
        problem_id = sub.get("ProblemID", "unknown")
        score = sub.get("Score", 0)
        attempt = sub.get("Attempt", "unknown")
        compile_result = sub.get("Compile.Result", "Unknown")

        parts.append(
            f"--- Submission {idx} ---\n"
            f"Student ID: {student_id}\n"
            f"Problem ID: {problem_id}\n"
            f"Score: {float(score) * 100:.1f}%\n"
            f"Attempt #: {attempt}\n"
            f"Compiled: {compile_result}\n\n"
            f"Code:\n```java\n{code}\n```\n"
        )

    parts.append(
        "\nAnalyze each student's knowledge state and predict future struggles."
    )
    return "\n".join(parts)


def clean_json_response(text: str) -> str:
    """Strip markdown code fences from a JSON response."""
    result = text.strip()
    if result.startswith("```json"):
        result = result[7:]
    if result.startswith("```"):
        result = result[3:]
    if result.endswith("```"):
        result = result[:-3]
    return result.strip()


# ---------------------------------------------------------------------------
# System instruction builder (delegates to lib.prompts)
# ---------------------------------------------------------------------------


def create_system_instruction(
    problem_ids: list[int] | None = None,
) -> str:
    """Build the Curriculum-Aware system instruction.

    Loads topics & problem descriptions on demand (no module-level I/O).
    """
    topics = load_topics_json()
    problems = load_problem_descriptions()
    ids = problem_ids or FOCUS_PROBLEMS
    return build_curriculum_aware_prompt(topics or {}, problems, ids)


# ---------------------------------------------------------------------------
# Core analysis functions
# ---------------------------------------------------------------------------


def analyze_student_submissions(
    submissions: list[dict],
    limit: int = 30,
    system_instruction: str | None = None,
) -> dict | None:
    """Send *submissions* to Gemini and return the parsed JSON result."""
    submissions = submissions[:limit]
    if not submissions:
        print("No submissions to analyze.")
        return None

    formatted_input = format_submissions(submissions)
    if system_instruction is None:
        system_instruction = create_system_instruction()

    print(f"Analyzing {len(submissions)} submissions...")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=formatted_input,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3,
            response_mime_type="application/json",
        ),
    )

    if response.text:
        try:
            return json.loads(clean_json_response(response.text))
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Raw response: {response.text[:500]}...")
    return None


# ---------------------------------------------------------------------------
# Data filtering helpers
# ---------------------------------------------------------------------------


def get_focused_best_attempts(
    problem_ids: list[int] | None = None,
    max_score: float = 0.9,
) -> list[dict]:
    """Load best attempts and filter to *problem_ids* with Score < *max_score*."""
    ids = problem_ids or FOCUS_PROBLEMS
    df = load_joined_datasets(verbose=False)
    if df is None:
        return []

    best_df = get_best_attempts(df, verbose=False)
    focused = best_df[best_df["ProblemID"].isin(ids)]
    struggling = focused[focused["Score"] < max_score]

    print(
        f"Focused on problems {ids}: "
        f"{len(struggling):,} struggling submissions "
        f"({struggling['SubjectID'].nunique()} students)"
    )
    return struggling.to_dict("records")


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------


def print_student_analysis(results: dict) -> None:
    """Pretty-print individual student analysis results."""
    if not results:
        print("No results to display.")
        return

    print("\n" + "=" * 70)
    print("INDIVIDUAL STUDENT ANALYSIS")
    print("=" * 70)

    for student in results.get("student_analysis", []):
        sid = student.get("student_id", "?")
        pid = student.get("problem_id", "?")
        score = student.get("score", 0)
        print(f"\nStudent {sid} | Problem {pid} | Score: {score}%")
        print("-" * 50)

        for gap in student.get("knowledge_gaps", []):
            sev = gap.get("severity", "unknown")
            icon = {"critical": "!!", "moderate": "! ",
                    "minor": "  "}.get(sev, "  ")
            print(f"  [{icon}] {gap.get('gap', 'N/A')}")
            print(f"       Evidence : {str(gap.get('evidence', ''))[:80]}")
            print(f"       Missing  : {gap.get('missing_concept', 'N/A')}")

        for pred in student.get("future_predictions", []):
            print(f"  -> At risk: {pred.get('at_risk_topic', 'N/A')}")
            print(f"     Reason : {pred.get('reason', 'N/A')}")

        intervention = student.get("recommended_intervention", "")
        if intervention:
            print(f"  Recommendation: {intervention}")

    summary = results.get("class_summary", {})
    if summary:
        print("\n" + "=" * 70)
        print("CLASS SUMMARY")
        print("=" * 70)
        for gap in summary.get("common_gaps", []):
            print(f"  - {gap}")
        at_risk = summary.get("highest_risk_students", [])
        if at_risk:
            print(f"  At-risk students: {', '.join(map(str, at_risk))}")
        for topic in summary.get("suggested_review_topics", []):
            print(f"  Review: {topic}")

    print("=" * 70)


# ---------------------------------------------------------------------------
# Pipeline orchestrator
# ---------------------------------------------------------------------------


def run_analysis(
    problem_ids: list[int] | None = None,
    max_students: int = 50,
    max_score: float = 0.9,
) -> dict | None:
    """End-to-end: load data -> filter -> call LLM -> print -> return results."""
    ids = problem_ids or FOCUS_PROBLEMS
    print(
        f"Analysis: problems={ids}, max_students={max_students}, max_score={max_score}")

    submissions = get_focused_best_attempts(
        problem_ids=ids, max_score=max_score)
    if not submissions:
        print("No submissions found.")
        return None

    results = analyze_student_submissions(submissions, limit=max_students)
    if results is None:
        raise RuntimeError("No results generated by LLM.")

    print_student_analysis(results)
    return results
