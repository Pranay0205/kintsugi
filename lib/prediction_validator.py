
import pandas as pd
from typing import List, Dict, Set
from utils.dataset import load_joined_datasets, load_problem_descriptions
from utils.constants import PROBLEM_PROMPT_PATH


def load_problem_topics() -> pd.DataFrame:
    """Loads the problem prompts csv which contains topic tags for each problem."""
    try:
        return pd.read_csv(PROBLEM_PROMPT_PATH)
    except Exception as e:
        print(f"Error loading problem topics: {e}")
        return None


def map_prediction_to_topics(prediction_text: str) -> List[str]:
    """
    Maps an LLM free-text prediction to the columns in problem_prompts.csv.
    This is a heuristic mapping.
    """
    text = prediction_text.lower()
    mapped_topics = []

    topic_mapping = {
        "loop": ["While", "For", "NestedFor"],
        "nestedloop": ["NestedFor"],
        "iteration": ["While", "For", "NestedFor"],
        "condition": ["If/Else", "NestedIf", "LogicBoolean"],
        "logic": ["LogicAndNotOr", "LogicCompareNum", "LogicBoolean"],
        "string": ["StringFormat", "StringConcat", "StringIndex", "StringLen", "StringEqual", "CharEqual"],
        "array": ["ArrayIndex"],
        "method": ["DefFunction"],
        "function": ["DefFunction"],
        "math": ["Math+-*/", "Math%"],
        "arithmetic": ["Math+-*/", "Math%"],
        "indexing": ["ArrayIndex", "StringIndex"],
        "comparison": ["LogicCompareNum", "StringEqual", "CharEqual"]
    }

    for key, columns in topic_mapping.items():
        if key in text:
            mapped_topics.extend(columns)

    return list(set(mapped_topics))


def validate_predictions(
    student_id: str,
    predictions: List[Dict],
    df_all: pd.DataFrame,
    problem_topics_df: pd.DataFrame
) -> Dict:
    """
    Validates predictions for a single student.

    Args:
        student_id: The student ID.
        predictions: List of prediction objects from LLM (e.g., [{'at_risk_topic': 'Loops'}]).
        df_all: The full joined dataset containing all events.
        problem_topics_df: DataFrame with problem topic tags.

    Returns:
        Dictionary containing validation stats.
    """

    # Get student's future submissions (we assume 'future' means problems NOT in the analyzed set)
    # Ideally we should filter by time, but for this prototype we'll look at "other problems"
    # or rely on the caller to split data.
    # For simplicity here, we look at *all* other problems the student attempted.

    student_data = df_all[df_all['SubjectID'] == student_id]

    matches = 0
    total_predictions = 0
    details = []

    for pred in predictions:
        topic_text = pred.get('at_risk_topic', '')
        if not topic_text:
            continue

        relevant_columns = map_prediction_to_topics(topic_text)

        if not relevant_columns:
            details.append({
                "prediction": topic_text,
                "result": "unknown_topic",
                "reason": "Could not map to dataset topics"
            })
            continue

        # Find problems validation set that have these topics
        # We need to filter problem_topics_df where any of relevant_columns == 1

        # Build query string
        query_parts = [
            f"`{col}` == 1" for col in relevant_columns if col in problem_topics_df.columns]
        if not query_parts:
            details.append({
                "prediction": topic_text,
                "result": "skipped",
                "reason": "Topic columns not found in dataset"
            })
            continue

        query = " or ".join(query_parts)
        target_problems_df = problem_topics_df.query(query)
        target_problem_ids = target_problems_df['ProblemID'].unique()

        # Check student performance on these problems
        # We look for "struggle": Average score < 0.8 or multiple attempts
        student_topic_perf = student_data[student_data['ProblemID'].isin(
            target_problems_df['ProblemID'])]

        if student_topic_perf.empty:
            details.append({
                "prediction": topic_text,
                "result": "no_data",
                "reason": "Student did not attempt future problems in this topic"
            })
            continue

        # Only count prediction if we have data to validate it
        total_predictions += 1

        # Calculate stats
        avg_score = student_topic_perf['Score'].mean()

        # Did they struggle? (Heuristic: avg score < 80%)
        did_struggle = avg_score < 0.8

        if did_struggle:
            matches += 1
            details.append({
                "prediction": topic_text,
                "result": "confirmed",
                "avg_score": float(avg_score),
                "reason": f"Low score ({avg_score:.2f}) on {len(student_topic_perf)} submissions"
            })
        else:
            details.append({
                "prediction": topic_text,
                "result": "refuted",
                "avg_score": float(avg_score),
                "reason": f"Good score ({avg_score:.2f}) on {len(student_topic_perf)} submissions"
            })

    return {
        "student_id": student_id,
        "total_predictions": total_predictions,
        "confirmed_matches": matches,
        "accuracy": matches / total_predictions if total_predictions > 0 else 0,
        "details": details
    }
