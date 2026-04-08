import pandas as pd
import os

def clean_pacific_universe():
    # Define the base path for our static file
    static_path = 'data/raw/Static.csv'
    
    if not os.path.exists(static_path):
        print("Error: Static.csv not found in data/raw")
        return
    
    # Load and filter for the PAC region only
    static_df = pd.read_csv(static_path)
    pacific_df = static_df[static_df['Region'].str.strip() == 'PAC'].copy()
    
    # Save the universe list to processed folder
    pacific_df.to_csv('data/processed/Pacific_Universe.csv', index=False)
    valid_isins = pacific_df['ISIN'].unique()
    print(f"Pacific universe created: {len(valid_isins)} companies identified.")

    # List of Datastream files to filter (Source -> Destination)
    files = [
        ('data/raw/DS_REV_USD_Y.csv', 'data/processed/Clean_Revenues_Pacific.csv'),
        ('data/raw/DS_CO2_SCOPE_1.csv', 'data/processed/Clean_Scope1_Pacific.csv'),
        ('data/raw/DS_RI_T_USD_M.csv', 'data/processed/Clean_Prices_Pacific.csv')
    ]

    for src, dest in files:
        if os.path.exists(src):
            # skiprows=[1] handles the Datastream error line ($$ER: E100)
            data = pd.read_csv(src, skiprows=[1])
            
            # Keep only rows belonging to our Pacific ISIN list
            filtered_data = data[data['ISIN'].isin(valid_isins)]
            filtered_data.to_csv(dest, index=False)
            print(f"Successfully created: {dest}")
        else:
            print(f"Warning: Source file {src} missing.")

if __name__ == "__main__":
    clean_pacific_universe()