import pandas as pd
import os

def fix_carbon_data():
    # The Excel file should be in data/raw/
    excel_input = "data/raw/DS_CO2_SCOPE_1_Y_2025.xlsx"
    csv_output = "data/raw/DS_CO2_SCOPE_1.csv"

    if os.path.exists(excel_input):
        try:
            # Check the first 10 rows to find the headers
            for i in range(10):
                df = pd.read_excel(excel_input, skiprows=i)
                if 'ISIN' in df.columns:
                    df = df.dropna(subset=['ISIN'])
                    df.to_csv(csv_output, index=False)
                    print(f"Success: {csv_output} created with {len(df)} rows.")
                    return
            print("Error: Could not find ISIN column in the Excel file.")
        except Exception as e:
            print(f"Read error: {e}")
    else:
        print(f"File not found: {excel_input}")

if __name__ == "__main__":
    fix_carbon_data()