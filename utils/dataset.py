

from utils.constants import MAINTABLE_PATH, CODESTATES_TABLE_PATH, PROBLEM_PROMPT_PATH, SUBJECT_TABLE_PATH, TOPICS_JSON_PATH
import pandas as pd
import json


def load_data():

    try:
        print("Loading datasets...")

        main_table = pd.read_csv(MAINTABLE_PATH)
        print(f"Main table: {len(main_table):,} rows")

        codestate_table = pd.read_csv(CODESTATES_TABLE_PATH)
        print(f"CodeState table: {len(codestate_table):,} rows")

        subject_table = pd.read_csv(SUBJECT_TABLE_PATH)
        print(f"Subject table: {len(subject_table):,} rows")

        return main_table, codestate_table, subject_table

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None, None, None


def load_joined_datasets():
    main_table, codestate_table, subject_table = load_data()

    if main_table is None or codestate_table is None or subject_table is None:
        print("Failed to load datasets. Aborting join operation.")
        return None

    print("\nJoining datasets...")
    data = main_table.merge(codestate_table, on="CodeStateID")

    full_data = data.merge(subject_table, on="SubjectID")
    print(f"Joined dataset: {len(full_data):,} rows")

    print("Datasets joined successfully.")

    print("Columns in the joined dataset:")
    print(full_data.columns)

    return full_data


def load_topics_json() -> dict | None:

    try:
        with open(TOPICS_JSON_PATH, 'r') as f:
            topics = json.load(f)
        print(f"Loaded topics from {TOPICS_JSON_PATH}")
        return topics
    except FileNotFoundError:
        print(f"Error: {TOPICS_JSON_PATH} not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {TOPICS_JSON_PATH}: {e}")
        return None

# utils/dataset.py or wherever you load data


def load_problem_descriptions() -> dict[str, str]:
    """
    Load problem descriptions from LinkTable.csv or wherever they're stored.
    Returns dict mapping problem_id -> problem_description
    """
    # Adjust path/column names based on your actual data
    problems_df = pd.read_csv(PROBLEM_PROMPT_PATH)

    problem_map = {}
    for _, row in problems_df.iterrows():
        problem_id = str(row['ProblemID'])
        description = row['Requirement']  # or whatever column has it
        problem_map[problem_id] = description

    return problem_map


def get_best_attempts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a DataFrame with only the best attempt (highest Score) 
    for each student-problem pair.

    If there are ties, takes the latest attempt (highest Attempt number).
    """
    # Filter to only Run.Program events (these have the Score)
    run_events = df[df['EventType'] == 'Run.Program'].copy()

    # Sort by Score (desc) then Attempt (desc) to handle ties
    run_events = run_events.sort_values(
        by=['SubjectID', 'ProblemID', 'Score', 'Attempt'],
        ascending=[True, True, False, False]
    )

    # Keep first row for each student-problem pair (which is now the best)
    best_attempts = run_events.groupby(
        ['SubjectID', 'ProblemID']).first().reset_index()

    print(f"Best attempts: {len(best_attempts):,} rows")
    print(f"  Unique students: {best_attempts['SubjectID'].nunique()}")
    print(f"  Unique problems: {best_attempts['ProblemID'].nunique()}")

    return best_attempts
