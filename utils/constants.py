"""Project-wide constants and configuration paths."""

import os

from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
MAINTABLE_PATH = os.path.join(
    PROJECT_ROOT, "dataset", "CodeWorkout", "MainTable.csv")
CODESTATES_TABLE_PATH = os.path.join(
    PROJECT_ROOT, "dataset", "CodeWorkout", "LinkTables", "CodeStates.csv")
SUBJECT_TABLE_PATH = os.path.join(
    PROJECT_ROOT, "dataset", "CodeWorkout", "LinkTables", "Subject.csv")
TOPICS_JSON_PATH = os.path.join(
    PROJECT_ROOT, "dataset", "Topics", "java_topics.json")
PROBLEM_PROMPT_PATH = os.path.join(
    PROJECT_ROOT, "dataset", "CodeWorkout", "Problem_Prompts", "problem_prompts.csv")

# API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Analysis defaults
BATCH_SIZE = 50
RATE_TIME_SECONDS = 4  # 15 RPM => 60/15 = 4 s between requests
FOCUS_PROBLEMS = [32, 33, 34]
VALIDATION_PROBLEMS = [36, 37, 38, 39, 40]
EARLY_STRUGGLE_THRESHOLD = 0.9
FUTURE_STRUGGLE_THRESHOLD = 0.8
