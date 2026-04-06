import pandas as pd
import os

# 1. Check the Static file for Region names
if os.path.exists("Static.csv"):
    df_static = pd.read_csv("Static.csv", encoding='latin1')
    df_static.columns = df_static.columns.str.strip()
    
    print("--- REGION ANALYSIS ---")
    if 'Region' in df_static.columns:
        unique_regions = df_static['Region'].unique()
        print(f"Unique regions found: {unique_regions}")
        
        # Flexible filter to catch 'Pacific', 'ASIA-PACIFIC', etc.
        pacific_df = df_static[df_static['Region'].str.contains('Pacific', na=False, case=False)]
        print(f"Firms matching 'Pacific': {len(pacific_df)}")
        
        if len(pacific_df) > 0:
            pacific_df.to_csv("Pacific_Universe.csv", index=False)
            print("Successfully created Pacific_Universe.csv")
    else:
        print(f"COLUMN 'Region' NOT FOUND. Available columns: {df_static.columns.tolist()}")

# 2. Search for the missing Revenue file
print("\n--- FILE SEARCH ---")
all_files = os.listdir('.')
rev_files = [f for f in all_files if 'REV' in f.upper()]
print(f"Potential Revenue files in your folder: {rev_files}")