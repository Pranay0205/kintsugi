"""Data loading and preprocessing for the CodeWorkout dataset."""

import json

import pandas as pd

from utils.constants import (
    MAINTABLE_PATH,
    CODESTATES_TABLE_PATH,
    PROBLEM_PROMPT_PATH,
    SUBJECT_TABLE_PATH,
    TOPICS_JSON_PATH,
)


def load_data(
    verbose: bool = False,
) -> tuple[pd.DataFrame | None, pd.DataFrame | None, pd.DataFrame | None]:
    """Load raw CSV tables (MainTable, CodeStates, Subject)."""
    try:
        main_table = pd.read_csv(MAINTABLE_PATH)
        codestate_table = pd.read_csv(CODESTATES_TABLE_PATH)
        subject_table = pd.read_csv(SUBJECT_TABLE_PATH)

        if verbose:
            print(f"Main table: {len(main_table):,} rows")
            print(f"CodeState table: {len(codestate_table):,} rows")
            print(f"Subject table: {len(subject_table):,} rows")

        return main_table, codestate_table, subject_table

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None, None, None


def load_joined_datasets(verbose: bool = True) -> pd.DataFrame | None:
    """Load and join all three tables into a single DataFrame (~191 k rows)."""
    main_table, codestate_table, subject_table = load_data(verbose=verbose)

    if main_table is None or codestate_table is None or subject_table is None:
        print("Failed to load datasets.")
        return None

    data = main_table.merge(codestate_table, on="CodeStateID")
    full_data = data.merge(subject_table, on="SubjectID")

    if verbose:
        print(f"Joined dataset: {len(full_data):,} rows")

    return full_data


def load_topics_json() -> dict | None:
    """Load the course curriculum topic structure from JSON."""
    try:
        with open(TOPICS_JSON_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading topics: {e}")
        return None


def load_problem_descriptions() -> dict[str, str]:
    """Return ``{problem_id: requirement_text}`` from problem_prompts.csv."""
    problems_df = pd.read_csv(PROBLEM_PROMPT_PATH)
    return {
        str(row["ProblemID"]): row["Requirement"]
        for _, row in problems_df.iterrows()
    }


def load_problem_topics() -> pd.DataFrame | None:
    """Load the problem → KC tag matrix from problem_prompts.csv."""
    try:
        return pd.read_csv(PROBLEM_PROMPT_PATH)
    except Exception as e:
        print(f"Error loading problem topics: {e}")
        return None


def get_best_attempts(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """Best attempt (highest Score) per student–problem pair.

    Ties are broken by latest Attempt number.
    Only ``Run.Program`` events are considered.
    """
    run_events = df[df["EventType"] == "Run.Program"].copy()

    run_events = run_events.sort_values(
        by=["SubjectID", "ProblemID", "Score", "Attempt"],
        ascending=[True, True, False, False],
    )

    best = run_events.groupby(["SubjectID", "ProblemID"]).first().reset_index()

    if verbose:
        print(
            f"Best attempts: {len(best):,} rows "
            f"({best['SubjectID'].nunique()} students, "
            f"{best['ProblemID'].nunique()} problems)"
        )

    return best
