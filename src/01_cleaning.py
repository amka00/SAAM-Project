import io
import os
import zipfile
import pandas as pd


def clean_pacific_universe():
    static_path = 'data/raw/Static.csv'
    if not os.path.exists(static_path):
        print("Error: Static.csv not found in data/raw")
        return

    static_df  = pd.read_csv(static_path)
    pacific_df = static_df[static_df['Region'].str.strip() == 'PAC'].copy()
    pacific_df.to_csv('data/processed/Pacific_Universe.csv', index=False)
    valid_isins = pacific_df['ISIN'].unique()
    print(f"Pacific universe created: {len(valid_isins)} companies identified.")

    # ── Standard CSV files (revenues + prices) ───────────────────────────────
    csv_files = [
        ('data/raw/DS_REV_USD_Y.csv',  'data/processed/Clean_Revenues_Pacific.csv'),
        ('data/raw/DS_RI_T_USD_M.csv', 'data/processed/Clean_Prices_Pacific.csv'),
    ]
    for src, dest in csv_files:
        if os.path.exists(src):
            data = pd.read_csv(src, skiprows=[1])   # skip Datastream $$ER row
            data[data['ISIN'].isin(valid_isins)].to_csv(dest, index=False)
            print(f"Successfully created: {dest}")
        else:
            print(f"Warning: {src} missing.")

    # ── CO2 Scope 1 & 2 — extracted from zip (flat CSV is empty) ─────────────
    zip_path = 'Data_2026.zip'
    co2_files = {
        'DS_CO2_SCOPE_1_Y_2025.xlsx': 'data/processed/Clean_CO2_Scope1_Pacific.csv',
        'DS_CO2_SCOPE_2_Y_2025.xlsx': 'data/processed/Clean_CO2_Scope2_Pacific.csv',
    }
    if os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for xlsx_name, dest in co2_files.items():
                with zf.open(xlsx_name) as f:
                    df = pd.read_excel(io.BytesIO(f.read()), skiprows=[1])
                df[df['ISIN'].isin(valid_isins)].reset_index(drop=True).to_csv(dest, index=False)
                print(f"Successfully created: {dest}")
    else:
        print(f"Warning: {zip_path} not found. CO2 files not created.")


if __name__ == "__main__":
    clean_pacific_universe()
