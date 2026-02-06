"""CLI sub-command: run batch LLM analysis on student submissions."""

from lib.llm_batch_analyzer import analyze_student_submissions, print_student_analysis
from utils.constants import BATCH_SIZE
from utils.dataset import load_joined_datasets


def analyze_command(limit: int = BATCH_SIZE) -> None:
    """Analyze Spring 2019 submissions using the Curriculum-Aware prompt."""
    data = load_joined_datasets()
    if data is None:
        return

    spring_2019 = data[data["TermID"] == "spring-2019"]
    submissions = spring_2019.to_dict(orient="records")

    print(f"\nAnalyzing {len(submissions):,} submissions from Spring 2019...")

    results = analyze_student_submissions(submissions, limit)
    if results:
        print_student_analysis(results)
    else:
        print("Failed to get analysis results.")
