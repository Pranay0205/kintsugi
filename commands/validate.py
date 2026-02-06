"""CLI sub-command: validate LLM predictions against future performance."""

import json
import random

from lib.llm_batch_analyzer import run_analysis
from lib.normalizer import normalize_predictions
from lib.prediction_validator import (
    validate_predictions,
    load_problem_topics,
    compute_binary_metrics,
)
from utils.constants import (
    FOCUS_PROBLEMS,
    VALIDATION_PROBLEMS,
    EARLY_STRUGGLE_THRESHOLD,
    FUTURE_STRUGGLE_THRESHOLD,
)
from utils.dataset import load_joined_datasets, get_best_attempts


def validate_command(limit: int = 30) -> None:
    """Run validation on a mixed sample of struggling + non-struggling students."""
    print(f"Running validation on {limit} students (mixed sample)...")

    # 1. Load data
    df_all = load_joined_datasets()
    if df_all is None:
        print("Failed to load datasets.")
        return

    best_df = get_best_attempts(df_all)
    problem_topics_df = load_problem_topics()
    if problem_topics_df is None:
        print("Failed to load problem topics.")
        return

    # 2. Build mixed sample
    focus_attempts = best_df[best_df["ProblemID"].isin(FOCUS_PROBLEMS)]
    future_attempts = best_df[best_df["ProblemID"].isin(VALIDATION_PROBLEMS)]
    future_avgs = future_attempts.groupby("SubjectID")["Score"].mean()

    struggling_early = set(
        focus_attempts[focus_attempts["Score"] <
                       EARLY_STRUGGLE_THRESHOLD]["SubjectID"]
    )
    struggling_future = set(
        future_avgs[future_avgs < FUTURE_STRUGGLE_THRESHOLD].index)
    persistent_struggling = list(struggling_early & struggling_future)

    non_struggling_early = set(
        focus_attempts[focus_attempts["Score"] >=
                       EARLY_STRUGGLE_THRESHOLD]["SubjectID"]
    )
    non_struggling_future = set(
        future_avgs[future_avgs >= FUTURE_STRUGGLE_THRESHOLD].index
    )
    confirmed_non_struggling = list(
        non_struggling_early & non_struggling_future)

    random.seed(42)
    half = limit // 2
    sampled_s = random.sample(
        persistent_struggling, min(half, len(persistent_struggling))
    )
    sampled_ns = random.sample(
        confirmed_non_struggling, min(
            limit - half, len(confirmed_non_struggling))
    )

    ground_truth = {sid: True for sid in sampled_s}
    ground_truth.update({sid: False for sid in sampled_ns})
    all_ids = sampled_s + sampled_ns

    print(
        f"Sample: {len(sampled_s)} struggling + {len(sampled_ns)} non-struggling "
        f"= {len(all_ids)} total"
    )

    # 3. Run LLM analysis
    print("\nGenerating predictions based on early problems...")
    analysis_results = run_analysis(
        problem_ids=FOCUS_PROBLEMS,
        max_students=limit,
        max_score=1.0,
    )

    if not analysis_results:
        print("Analysis failed.")
        return

    # 4. Validate
    df_future = best_df[best_df["ProblemID"].isin(VALIDATION_PROBLEMS)]
    binary_rows = []

    print("\nValidating Predictions Against Future Performance...")
    print("=" * 60)

    for student_analysis in analysis_results.get("student_analysis", []):
        student_id = student_analysis.get("student_id")
        if student_id not in ground_truth:
            continue

        predictions = normalize_predictions(
            student_analysis.get("future_predictions", [])
        )

        stats = validate_predictions(
            student_id=student_id,
            predictions=predictions,
            df_all=df_future,
            problem_topics_df=problem_topics_df,
        )

        gt = ground_truth[student_id]
        binary_rows.append({
            "strategy": "default",
            "student_id": student_id,
            "predicted_struggle": stats["predicted_struggle"],
            "actual_struggle": gt,
        })

        label = "STRUGGLING" if gt else "NON-STRUGGLING"
        print(
            f"Student {student_id} [{label}]: Accuracy {stats['accuracy']:.1%} "
            f"({stats['confirmed_matches']}/{stats['total_predictions']})"
        )
        for det in stats["details"]:
            icon = {"confirmed": "+", "refuted": "-"}.get(det["result"], "?")
            print(
                f"   [{icon}] '{det.get('normalized', det['prediction'])}' -> {det['result']}")

    # 5. Compute Metrics
    metrics = compute_binary_metrics(binary_rows)
    print("\n" + "=" * 60)
    print("BINARY CLASSIFICATION METRICS")
    print(
        f"  TP={metrics['tp']}  FP={metrics['fp']}  FN={metrics['fn']}  TN={metrics['tn']}")
    print(f"  Precision: {metrics['precision']:.3f}")
    print(f"  Recall:    {metrics['recall']:.3f}")
    print(f"  F1-Score:  {metrics['f1']:.3f}")
    print(f"  Accuracy:  {metrics['accuracy']:.3f}")
    print("=" * 60)
