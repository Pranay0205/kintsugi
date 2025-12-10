

from constants import MAINTABLE_PATH, CODESTATES_TABLE_PATH, SUBJECT_TABLE_PATH
import pandas as pd


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
   
  

def join_datasets():
  main_table, codestate_table, subject_table = load_data()
  
  if main_table is None or codestate_table is None or subject_table is None:
    print("Failed to load datasets. Aborting join operation.")
    return None
  
  print("\nJoining datasets...")
  data = main_table.merge(codestate_table, on="CodeStateID")

  full_data = data.merge(subject_table, on="SubjectID")
  print(f"Joined dataset: {len(full_data):,} rows")
  
  print("Datasets joined successfully.")
  
  print("\nSample of joined data:")
  print(full_data.head()) 
  
  print("\nInformation about joined data:")
  print(full_data.info())
  
  
  return full_data


  
  
join_datasets()
