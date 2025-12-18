import json
from typing import Hashable
from google import genai
from google.genai import types
from utils.api_utils import rate_limit
from utils.constants import BATCH_SIZE, GEMINI_API_KEY
from utils.dataset import load_topics_json, load_problem_descriptions


client = genai.Client(api_key=GEMINI_API_KEY)

# Load curriculum and problems
topics = load_topics_json()
problems = load_problem_descriptions()


system_instruction = f"""You are analyzing Java code submissions from CS 1114 to identify knowledge gaps.

COURSE CURRICULUM:
{json.dumps(topics, indent=2)}

PROBLEM DESCRIPTIONS:
{json.dumps(problems, indent=2)}

YOUR TASK:
Analyze student code submissions and identify the top 3-5 knowledge gaps affecting the class.

ANALYSIS APPROACH:
1. Match each submission to its problem using Problem ID
2. Identify common error patterns across multiple students
3. Determine which curriculum topics would address these errors
4. Prioritize gaps by impact (how many students affected, how critical to learning progression)

RULES:
1. Map gaps to curriculum topics (use exact topic names)
2. Prefer chapter-level or broader topics over specific method names
3. Group related issues together
4. Only report patterns affecting multiple students (ignore isolated errors)
5. Consider both syntax errors AND logic errors
6. Distinguish between "many students make this error" vs "this error blocks progress"

FREQUENCY GUIDELINES:
- high: Affects 40%+ of students
- medium: Affects 15-40% of students  
- low: Affects <15% of students (only report if critically important)

OUTPUT FORMAT:
Return ONLY valid JSON:
{{
  "knowledge_gaps": [
    {{
      "gap": "Clear description of what students are doing wrong",
      "frequency": "high/medium/low",
      "curriculum_topics": ["Topic from curriculum"],
      "chapter": "Chapter number"
    }}
  ]
}}

FOCUS ON: Actionable insights for the instructor to improve teaching.
"""

# Create cache
cache = client.caches.create(
    model="gemini-2.5-flash",
    config=types.CreateCachedContentConfig(
        system_instruction=system_instruction,
        contents=[]
    )
)

print(f"Cache created: {cache.name}")
print(f"Cached: Curriculum + {len(problems)} problems + Instructions")


def analyze_batch_submissions(submissions: list[dict[Hashable, str]], limit: int = BATCH_SIZE) -> dict | None:

    formatted_submissions = format_input_for_batch(submissions[:limit])

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=formatted_submissions,  # Only this changes between calls
        config=types.GenerateContentConfig(
            cached_content=cache.name,
            temperature=0.3,
            response_mime_type="application/json"
        )
    )

    if response.text:
        result = response.text.strip()
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

    formatted = "SUBMISSIONS:\n\n"

    for idx, submission in enumerate(submissions, 1):
        code = submission.get('Code', '')
        student_id = submission.get('SubjectID', 'unknown')
        problem_id = submission.get('ProblemID', 'unknown')
        score = submission.get('X-Grade', 'unknown')

        formatted += f"""Submission {idx}:
Student: {student_id}
Problem ID: {problem_id}
Score: {float(score) * 100}%

Code:
{code}

---

"""

    return formatted


def print_analysis_results(results: dict) -> None:
    """Print knowledge gap analysis."""
    if not results:
        print("No results.")
        return

    print("\n" + "=" * 60)
    print("KNOWLEDGE GAP ANALYSIS")
    print("=" * 60)

    gaps = results.get("knowledge_gaps", [])
    for i, gap in enumerate(gaps, 1):
        print(f"\n{i}. {gap.get('gap', 'N/A')}")
        print(f"   Frequency: {gap.get('frequency', 'N/A')}")
        print(f"   Chapter: {gap.get('chapter', 'N/A')}")

        topics = gap.get("curriculum_topics", [])
        if topics:
            print(f"   Topics:")
            for topic in topics:
                print(f"      - {topic}")

    print("\n" + "=" * 60)
