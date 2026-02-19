import pandas as pd
import sys

try:
    # Attempt to find ProblemID 24
    for chunk in pd.read_csv('dataset/CodeWorkout/MainTable.csv', chunksize=5000):
        # Check if 24 is in this chunk's ProblemID column
        # Depending on CSV format, ProblemID might be string or int.
        # Let's check columns first if unsure, but based on grep it looks like a column.

        # It seems the grep showed `2.0,32,24`. The columns might be ordered.
        # Let's look for ProblemID column.
        if 'ProblemID' in chunk.columns:
            matches = chunk[chunk['ProblemID'] == 24]
            if not matches.empty:
                print(matches.iloc[0]['Code'])
                sys.exit(0)
        else:
            print("ProblemID column not found in chunk columns:", chunk.columns)
            break
except Exception as e:
    print(f"Error: {e}")
