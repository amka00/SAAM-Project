import pandas as pd
import os

def clean_and_filter_data():
    # On cherche dans data/raw
    if not os.path.exists('data/raw/Static.csv'):
        print("Erreur: Static.csv introuvable dans data/raw")
        return
    
    static = pd.read_csv('data/raw/Static.csv')
    pacific_universe = static[static['Region'].str.strip() == 'PAC'].copy()
    pacific_universe.to_csv('data/processed/Pacific_Universe.csv', index=False)
    
    valid_isins = pacific_universe['ISIN'].unique()

    # Mapping des fichiers (Source -> Destination)
    to_process = [
        ('data/raw/DS_REV_USD_Y.csv', 'data/processed/Clean_Revenues_Pacific.csv'),
        ('data/raw/DS_CO2_SCOPE_1.csv', 'data/processed/Clean_Scope1_Pacific.csv'),
        ('data/raw/DS_RI_T_USD_M.csv', 'data/processed/Clean_Prices_Pacific.csv')
    ]

    for src, out in to_process:
        if os.path.exists(src):
            df = pd.read_csv(src, skiprows=[1])
            df_filtered = df[df['ISIN'].isin(valid_isins)]
            df_filtered.to_csv(out, index=False)
            print(f"Créé: {out}")

if __name__ == "__main__":
    clean_and_filter_data()