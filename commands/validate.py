
from lib.llm_batch_analyzer import run_analysis
from lib.prediction_validator import validate_predictions, load_problem_topics
from utils.dataset import load_joined_datasets
import json


def validate_command(limit: int = 10):
    print(f"Running validation on top {limit} students...")

    # 1. Run Analysis (Simulation)
    # We focus on a few problems to act as the "Early" signal
    EARLY_PROBLEMS = [32, 33, 34]

    print("Generating predictions based on early problems...")
    analysis_results = run_analysis(
        problem_ids=EARLY_PROBLEMS,
        max_students=limit,
        max_score=1.0  # Analyze everyone to get a mix
    )

    if not analysis_results:
        print("Analysis failed.")
        return

    # 2. Load Validation Data
    df_all = load_joined_datasets()
    problem_topics_df = load_problem_topics()

    if df_all is None or problem_topics_df is None:
        print("Failed to load validation datasets.")
        return

    validation_stats = []

    # 3. Validate each student
    print("\n🔍 Validating Predictions Against Future Performance...")
    print("="*60)

    for student_analysis in analysis_results.get("student_analysis", []):
        student_id = student_analysis.get("student_id")
        predictions = student_analysis.get("future_predictions", [])

        # We need to filter the dataframe to EXCLUDE the problems we used for analysis
        # So we are validating on *unseen* data
        df_future = df_all[~df_all['ProblemID'].isin(EARLY_PROBLEMS)]

        stats = validate_predictions(
            student_id=student_id,
            predictions=predictions,
            df_all=df_future,
            problem_topics_df=problem_topics_df
        )

        validation_stats.append(stats)

        # Print inline result
        print(
            f"Student {student_id}: Accuracy {stats['accuracy']:.1%} ({stats['confirmed_matches']}/{stats['total_predictions']})")
        for det in stats['details']:
            icon = "✅" if det['result'] == 'confirmed' else "❌" if det['result'] == 'refuted' else "⚠️"
            print(
                f"   {icon} Predicted: '{det['prediction']}' -> {det['result']} ({det['reason']})")

    # 4. Overall Summary
    total_acc = sum(s['accuracy'] for s in validation_stats) / \
        len(validation_stats) if validation_stats else 0
    print("\n" + "="*60)
    print(f"📈 OVERALL PREDICTION ACCURACY: {total_acc:.1%}")
    print("="*60)
