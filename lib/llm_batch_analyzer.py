import json
from typing import Hashable
from google import genai

from utils.api_utils import rate_limit
from utils.constants import BATCH_SIZE, GEMINI_API_KEY


client = genai.Client(api_key=GEMINI_API_KEY)


def analyze_batch_submissions(submissions: list[dict[Hashable, str]], limit: int = BATCH_SIZE) -> dict | None:
    prompt = """Analyze these Java code submissions from a CS course.
              Return ONLY JSON with this structure:
              {
                "common_issues": [
                  {
                    "issue": "brief description",
                    "frequency": "high/medium/low",
                    "acm_topic": "relevant ACM CS curriculum topic",
                    "concept": "underlying concept students misunderstand"
                  }
                ],
                "recommended_topics": ["list of topics to review"]
              }

              Focus on: syntax errors, array/loop bounds, variable scope, return statements.

              Submissions:
              """
    formatted_submissions = format_input_for_batch(submissions[:limit])
    rate_limit()
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt + formatted_submissions)

    if response.text:
        result = response.text.strip()
        # Remove markdown code blocks if present
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
        result = result.strip()

        try:
            return json.loads(result)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return None
    return None


def format_input_for_batch(submissions: list[dict[Hashable, str]]) -> str:
    formatted_submissions = ""
    for submission in submissions:
        code = submission.get('Code', '')
        student_id = submission.get('SubjectID', 'unknown')
        formatted_submission = f"Student ID: {student_id}\nCode:\n{code}\n---\n"
        formatted_submissions += formatted_submission
    return formatted_submissions


def print_analysis_results(results: dict) -> None:
    if not results:
        print("No results to display.")
        return

    print("\n" + "=" * 60)
    print("CLASS ANALYSIS SUMMARY")
    print("=" * 60)

    # Print common issues
    common_issues = results.get("common_issues", [])
    if common_issues:
        print(f"\n📋 COMMON ISSUES ({len(common_issues)} found)\n")
        for i, issue in enumerate(common_issues, 1):
            frequency = issue.get("frequency", "unknown")
            frequency_icon = {"high": "🔴", "medium": "🟡",
                              "low": "🟢"}.get(frequency, "⚪")

            print(f"{i}. {issue.get('issue', 'N/A')}")
            print(f"   {frequency_icon} Frequency: {frequency.upper()}")
            print(f"   📚 ACM Topic: {issue.get('acm_topic', 'N/A')}")
            print(f"   💡 Concept: {issue.get('concept', 'N/A')}")
            print()

    # Print recommended topics
    recommended = results.get("recommended_topics", [])
    if recommended:
        print("-" * 60)
        print("📖 RECOMMENDED TOPICS TO REVIEW")
        print("-" * 60)
        for i, topic in enumerate(recommended, 1):
            print(f"   {i}. {topic}")

    print("\n" + "=" * 60)
