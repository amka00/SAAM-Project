import openpyxl
import pandas as pd
import os
import numpy as np
from pathlib import Path



# 1. FILE MAPPING - Standardizing names for the Pacific Scope 1 Strategy
file_mapping = {
    "Static_2025.xlsx": "Static.csv",
    "DS_CO2_SCOPE_1_Y_2025.xlsx": "DS_CO2_SCOPE_1.csv",
    "DS_REV_Y_2025.xlsx": "DS_REV_USD_Y.csv",
    "DS_RI_T_USD_M_2025.xlsx": "DS_RI_T_USD_M.csv",
    "DS_MV_T_USD_M_2025.xlsx": "DS_MV_T_USD_M.csv",
    "DS_RI_T_USD_Y_2025.xlsx": "DS_RI_T_USD_Y.csv",
    "DS_MV_T_USD_Y_2025.xlsx": "DS_MV_T_USD_Y.csv",
    "Risk_Free_Rate_2025.xlsx": "Risk_Free_Rate.csv"
}

def clean_price_data(value):
    """Rule: Treat prices below 0.5 as missing values[cite: 73]."""
    try:
        float_val = float(value)
        return np.nan if float_val < 0.5 else float_val
    except (ValueError, TypeError):
        return value

def process_and_standardize():
    for original, standard in file_mapping.items():
        if os.path.exists(original):
            try:
                df = pd.read_excel(original, engine='openpyxl')
                
                # Check for headers if Datastream junk is at the top [cite: 58, 61]
                if 'ISIN' not in df.columns and 'Region' not in df.columns:
                    for i in range(1, 11):
                        temp_df = pd.read_excel(original, skiprows=i)
                        if 'ISIN' in temp_df.columns or 'Region' in temp_df.columns:
                            df = temp_df
                            break

                # Apply 0.5 price floor to Monthly Return Index [cite: 73]
                if "RI_T_USD_M" in standard:
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    for col in numeric_cols:
                        df[col] = df[col].map(clean_price_data)
                
                df.to_csv(standard, index=False)
                print(f"Successfully converted: {standard}")
            except Exception as e:
                print(f"Error processing {original}: {e}")
        else:
            print(f"Warning: File not found -> {original}")

def prepare_pacific_universe():
    """Filters the Static file for the 'PAC' region[cite: 87, 95]."""
    if os.path.exists("Static.csv"):
        df = pd.read_csv("Static.csv")
        df.columns = df.columns.str.strip()
        
        if 'Region' in df.columns:
            # Filters for the assigned Pacific region code [cite: 26, 95]
            pacific_df = df[df['Region'].str.strip() == 'PAC']
            pacific_df.to_csv("Pacific_Universe.csv", index=False)
            # Fixed the unterminated f-string below:
            print(f"Success! Created Pacific_Universe.csv with {len(pacific_df)} firms.")
        else:
            print(f"Error: 'Region' column not found. Available: {df.columns.tolist()}")

if __name__ == "__main__":
    process_and_standardize()
    prepare_pacific_universe()