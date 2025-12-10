import os


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
print(f"Project Root Folder: {PROJECT_ROOT}")
MAINTABLE_PATH = os.path.join(PROJECT_ROOT, "dataset", "CodeWorkout", "MainTable.csv")
CODESTATES_TABLE_PATH = os.path.join(PROJECT_ROOT, "dataset", "CodeWorkout", "LinkTables", "CodeStates.csv")
SUBJECT_TABLE_PATH = os.path.join(PROJECT_ROOT, "dataset", "CodeWorkout", "LinkTables", "Subject.csv")