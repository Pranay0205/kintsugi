"""Validates LLM predictions against actual future student performance.

Provides:
- Per-prediction validation against the CodeWorkout dataset
- Binary classification metrics (Precision, Recall, F1)
- Strategy-level metric aggregation
"""

import pandas as pd
from typing import Dict, List
from collections import defaultdict

from lib.normalizer import (
    normalize_gap_tag,
    normalize_predictions,
    map_prediction_to_topic_columns,
)
from utils.constants import PROBLEM_PROMPT_PATH


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_problem_topics() -> pd.DataFrame | None:
    """Load the problem -> KC tag matrix from problem_prompts.csv."""
    try:
        return pd.read_csv(PROBLEM_PROMPT_PATH)
    except Exception as e:
        print(f"Error loading problem topics: {e}")
        return None


# ---------------------------------------------------------------------------
# Per-student prediction validation
# ---------------------------------------------------------------------------


def validate_predictions(
    student_id: str,
    predictions: List[Dict],
    df_all: pd.DataFrame,
    problem_topics_df: pd.DataFrame,
) -> Dict:
    """Validate predictions for a single student against future performance.

    Returns a dict with per-prediction details and a binary
    ``predicted_struggle`` flag based on confirmation rate >= 50%.
    """
    student_data = df_all[df_all["SubjectID"] == student_id]

    matches = 0
    total_predictions = 0
    details = []

    for pred in predictions:
        topic_text = pred.get("at_risk_topic", "") or pred.get("topic_tag", "")
        if not topic_text:
            continue

        relevant_columns = map_prediction_to_topic_columns(topic_text)

        if not relevant_columns:
            details.append({
                "prediction": topic_text,
                "normalized": normalize_gap_tag(topic_text),
                "result": "unknown_topic",
                "reason": "Could not map to dataset topics",
            })
            continue

        query_parts = [
            f"`{col}` == 1"
            for col in relevant_columns
            if col in problem_topics_df.columns
        ]
        if not query_parts:
            details.append({
                "prediction": topic_text,
                "normalized": normalize_gap_tag(topic_text),
                "result": "skipped",
                "reason": "Topic columns not found in dataset",
            })
            continue

        query = " or ".join(query_parts)
        target_problems_df = problem_topics_df.query(query)

        student_topic_perf = student_data[
            student_data["ProblemID"].isin(target_problems_df["ProblemID"])
        ]

        if student_topic_perf.empty:
            details.append({
                "prediction": topic_text,
                "normalized": normalize_gap_tag(topic_text),
                "result": "no_data",
                "reason": "Student did not attempt future problems in this topic",
            })
            continue

        total_predictions += 1
        avg_score = student_topic_perf["Score"].mean()
        did_struggle = avg_score < 0.8

        if did_struggle:
            matches += 1
            details.append({
                "prediction": topic_text,
                "normalized": normalize_gap_tag(topic_text),
                "result": "confirmed",
                "avg_score": float(avg_score),
                "reason": f"Low score ({avg_score:.2f}) on {len(student_topic_perf)} submissions",
            })
        else:
            details.append({
                "prediction": topic_text,
                "normalized": normalize_gap_tag(topic_text),
                "result": "refuted",
                "avg_score": float(avg_score),
                "reason": f"Good score ({avg_score:.2f}) on {len(student_topic_perf)} submissions",
            })

    # Binary classification: LLM predicts struggle when >= 50% of its
    # verifiable predictions are confirmed by poor future scores.
    confirmation_rate = matches / total_predictions if total_predictions > 0 else 0.0
    predicted_struggle = confirmation_rate >= 0.5

    return {
        "student_id": student_id,
        "total_predictions": total_predictions,
        "confirmed_matches": matches,
        "accuracy": confirmation_rate,
        "predicted_struggle": predicted_struggle,
        "details": details,
    }


# ---------------------------------------------------------------------------
# Binary classification metrics
# ---------------------------------------------------------------------------


def compute_binary_metrics(validation_rows: List[Dict]) -> Dict:
    """Compute Precision, Recall, F1, and Accuracy from validation rows.

    Each row must contain:
        - ``predicted_struggle`` (bool): LLM prediction
        - ``actual_struggle``   (bool): ground-truth label
    """
    tp = fp = fn = tn = 0

    for row in validation_rows:
        pred = bool(row.get("predicted_struggle", False))
        actual = bool(row.get("actual_struggle", False))

        if pred and actual:
            tp += 1
        elif pred and not actual:
            fp += 1
        elif not pred and actual:
            fn += 1
        else:
            tn += 1

    n = tp + fp + fn + tn
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          ) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / n if n > 0 else 0.0

    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "accuracy": round(accuracy, 4),
        "n": n,
    }


def compute_metrics_by_strategy(validation_rows: List[Dict]) -> Dict[str, Dict]:
    """Group validation rows by ``strategy`` and compute metrics per group."""
    by_strategy: Dict[str, List[Dict]] = defaultdict(list)

    for row in validation_rows:
        by_strategy[row["strategy"]].append(row)

    return {
        strategy: compute_binary_metrics(rows)
        for strategy, rows in by_strategy.items()
    }
