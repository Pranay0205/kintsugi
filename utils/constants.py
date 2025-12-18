import os

from dotenv import load_dotenv

load_dotenv()
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
print(f"Project Root Folder: {PROJECT_ROOT}")
MAINTABLE_PATH = os.path.join(
    PROJECT_ROOT, "dataset", "CodeWorkout", "MainTable.csv")
CODESTATES_TABLE_PATH = os.path.join(
    PROJECT_ROOT, "dataset", "CodeWorkout", "LinkTables", "CodeStates.csv")
SUBJECT_TABLE_PATH = os.path.join(
    PROJECT_ROOT, "dataset", "CodeWorkout", "LinkTables", "Subject.csv")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BATCH_SIZE = 50
RATE_TIME_SECONDS = 4  # 15 requests per minute => 60/15 = 4 seconds between requests
TOPICS_JSON_PATH = os.path.join(
    PROJECT_ROOT, "dataset", "Topics", "java_topics.json")

PROBLEM_PROMPT_PATH = os.path.join(
    PROJECT_ROOT,  "dataset", "CodeWorkout", "problem_prompts.csv")
