
import io
import zipfile
import pandas as pd
import os

# -- Paths --
ZIP_PATH       = "Data_2026.zip"
UNIVERSE_PATH  = "data/processed/Pacific_Universe.csv"
OUT_SCOPE1     = "data/processed/Clean_CO2_Scope1_Pacific.csv"
OUT_SCOPE2     = "data/processed/Clean_CO2_Scope2_Pacific.csv"

SCOPE_FILES = {
    "Scope 1": ("DS_CO2_SCOPE_1_Y_2025.xlsx", OUT_SCOPE1),
    "Scope 2": ("DS_CO2_SCOPE_2_Y_2025.xlsx", OUT_SCOPE2),
}

# Step 1: Load Pacific ISIN universe
universe = pd.read_csv(UNIVERSE_PATH)
pacific_isins = set(universe["ISIN"].unique())
print(f"Pacific universe: {len(pacific_isins)} ISINs loaded.\n")

# Step 2: Extract, clean, and filter each CO2 file
results = {}

with zipfile.ZipFile(ZIP_PATH, "r") as zf:
    for scope_label, (xlsx_name, csv_out) in SCOPE_FILES.items():
        print(f"Processing {scope_label} - {xlsx_name}")

        with zf.open(xlsx_name) as f:
            raw_bytes = f.read()

        # Row 1 contains the Datastream "$$ER: E100" error line - drop it
        df = pd.read_excel(io.BytesIO(raw_bytes), skiprows=[1])

        # Keep only Pacific ISINs
        df = df[df["ISIN"].isin(pacific_isins)].reset_index(drop=True)

        df.to_csv(csv_out, index=False)
        print(f"  Saved: {csv_out}  ({len(df)} companies)\n")
        results[scope_label] = df

# Step 3: NaN check for years < 2013
print("=" * 60)
print("NaN check - columns for years BEFORE 2013")
print("=" * 60)

for scope_label, df in results.items():
    year_cols = [c for c in df.columns if str(c).isdigit() and int(c) < 2013]

    if not year_cols:
        print(f"\n{scope_label}: no year columns found before 2013.")
        continue

    sub = df[["ISIN"] + year_cols]
    nan_mask = sub[year_cols].isna()

    total_cells = nan_mask.size
    total_nans  = int(nan_mask.sum().sum())
    pct_nan     = total_nans / total_cells * 100 if total_cells else 0

    print(f"\n{'_'*40}")
    print(f"{scope_label} | years: {year_cols[0]} - {year_cols[-1]}")
    print(f"  Companies: {len(df)}")
    print(f"  Total cells (company x year): {total_cells}")
    print(f"  NaN cells  : {total_nans}  ({pct_nan:.1f}%)")

    nan_by_year = nan_mask.sum().rename("NaN_count").to_frame()
    nan_by_year["pct"] = (nan_by_year["NaN_count"] / len(df) * 100).round(1)
    print("\n  NaN count per year:")
    print(nan_by_year.to_string())

    companies_with_nan = sub[nan_mask.any(axis=1)]["ISIN"].tolist()
    print(f"\n  Companies with at least one NaN before 2013: {len(companies_with_nan)}")
    if companies_with_nan:
        print("  Sample (up to 10):", companies_with_nan[:10])

print("\nDone.")
