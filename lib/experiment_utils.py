import json
import time
import random
from typing import Callable

import pandas as pd
from google import genai
from google.genai import types

import lib.prompts
from lib.llm_batch_analyzer import format_submissions, clean_json_response
from utils.constants import GEMINI_API_KEY
from utils.dataset import (
    load_joined_datasets,
    get_best_attempts,
    load_topics_json,
    load_problem_descriptions,
)


def create_client() -> genai.Client:
    return genai.Client(api_key=GEMINI_API_KEY)


def load_best_attempts_df() -> pd.DataFrame:
    df = load_joined_datasets()
    if df is None:
        raise ValueError("Failed to load joined datasets.")
    return get_best_attempts(df)


def select_target_student_id(
    best_attempts_df: pd.DataFrame,
    target_student_id: str | int | None = None,
    min_submissions: int = 5,
    struggling_threshold: float = 0.6,
):
    if target_student_id is not None:
        return target_student_id

    submission_counts = best_attempts_df.groupby("SubjectID").size()
    student_scores = best_attempts_df.groupby(
        "SubjectID")["Score"].mean().sort_values()

    students_with_enough_data = submission_counts[submission_counts >=
                                                  min_submissions].index
    struggling_students = student_scores[student_scores <
                                         struggling_threshold].index
    valid_candidates = [
        s for s in struggling_students if s in students_with_enough_data]

    return valid_candidates[0] if valid_candidates else student_scores.index[0]


def select_cohort_ids(
    best_attempts_df: pd.DataFrame,
    batch_size: int = 50,
    min_submissions: int = 5,
    seed: int = 42,
) -> list:
    submission_counts = best_attempts_df.groupby("SubjectID").size()
    eligible_ids = submission_counts[submission_counts >=
                                     min_submissions].index.tolist()
    if not eligible_ids:
        return []

    rng = random.Random(seed)
    return rng.sample(eligible_ids, min(batch_size, len(eligible_ids)))


def get_student_data(best_attempts_df: pd.DataFrame, student_id) -> pd.DataFrame:
    return (
        best_attempts_df[best_attempts_df["SubjectID"] == student_id]
        .copy()
        .sort_values(["ProblemID"])
        .reset_index(drop=True)
    )


def get_representative_rows_per_student(df: pd.DataFrame, student_ids: list) -> pd.DataFrame:
    rows = []
    for sid in student_ids:
        sid_rows = df[df["SubjectID"] == sid]
        if sid_rows.empty:
            continue
        rows.append(sid_rows.sort_values(["Score", "ProblemID"]).iloc[0])
    if not rows:
        return pd.DataFrame(columns=df.columns)
    return pd.DataFrame(rows)


def build_strategies(focus_problem_ids: list[int] | None = None) -> dict[str, Callable[[], str]]:
    topics = load_topics_json() or {}
    problem_descriptions = load_problem_descriptions() or {}
    ids = focus_problem_ids or []

    def curriculum_prompt() -> str:
        return lib.prompts.build_curriculum_aware_prompt(topics, problem_descriptions, ids)

    return {
        "Zero-Shot": lib.prompts.get_zero_shot_prompt,
        "Few-Shot": lib.prompts.get_few_shot_prompt,
        "Chain-of-Thought": lib.prompts.get_chain_of_thought_prompt,
        "Curriculum-Aware": curriculum_prompt,
    }


def analyze_submission_row(
    submission_row,
    client: genai.Client,
    model_id: str,
    strategies: dict[str, Callable[[], str]],
    temperature: float = 0.3,
) -> dict:
    results = {
        "SubjectID": submission_row.get("SubjectID"),
        "ProblemID": submission_row["ProblemID"],
        "Score": submission_row["Score"],
        "Code": submission_row["Code"],
    }

    formatted_input = format_submissions([submission_row.to_dict()])

    for strategy_name, prompt_func in strategies.items():
        start_t = time.time()
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=formatted_input,
                config=types.GenerateContentConfig(
                    system_instruction=prompt_func(),
                    temperature=temperature,
                    response_mime_type="application/json",
                ),
            )

            if response.text:
                parsed = json.loads(clean_json_response(response.text))
                results[f"{strategy_name}_Output"] = parsed
            else:
                results[f"{strategy_name}_Output"] = "No Response"
        except Exception as e:
            results[f"{strategy_name}_Output"] = f"Error: {str(e)}"

        results[f"{strategy_name}_TimeSec"] = round(time.time() - start_t, 3)

    return results


def run_experiment_rows(
    rows_df: pd.DataFrame,
    client: genai.Client,
    model_id: str,
    strategies: dict[str, Callable[[], str]],
    sleep_seconds: float = 1.0,
) -> pd.DataFrame:
    output_rows = []
    for _, row in rows_df.iterrows():
        output_rows.append(
            analyze_submission_row(
                submission_row=row,
                client=client,
                model_id=model_id,
                strategies=strategies,
            )
        )
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
    return pd.DataFrame(output_rows)


def build_strategy_summary(results_df: pd.DataFrame, strategies: dict[str, Callable[[], str]]) -> pd.DataFrame:
    summary_rows = []
    for strategy in strategies.keys():
        output_col = f"{strategy}_Output"
        time_col = f"{strategy}_TimeSec"

        if output_col not in results_df.columns:
            continue

        valid_count = results_df[output_col].apply(
            lambda x: not (isinstance(x, str) and x.startswith("Error:"))
        ).sum()
        total_count = len(results_df)

        summary_rows.append(
            {
                "Strategy": strategy,
                "Valid_Responses": int(valid_count),
                "Total_Responses": int(total_count),
                "Coverage_Pct": round((valid_count / total_count) * 100, 1)
                if total_count
                else 0.0,
                "Avg_Time_Sec": round(results_df[time_col].mean(), 3)
                if time_col in results_df.columns
                else None,
            }
        )

    return pd.DataFrame(summary_rows).sort_values(
        by=["Coverage_Pct", "Avg_Time_Sec"], ascending=[False, True]
    )


def save_results(df: pd.DataFrame, csv_path: str) -> str:
    df.to_csv(csv_path, index=False)
    return csv_path
