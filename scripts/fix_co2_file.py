import pandas as pd
import os

def fix_co2_data():
    # On pointe vers le nouveau dossier raw
    excel_source = "data/raw/DS_CO2_SCOPE_1_Y_2025.xlsx"
    csv_output = "data/raw/DS_CO2_SCOPE_1.csv"

    if os.path.exists(excel_source):
        try:
            for i in range(10):
                df = pd.read_excel(excel_source, skiprows=i)
                if 'ISIN' in df.columns:
                    df = df.dropna(subset=['ISIN'])
                    df.to_csv(csv_output, index=False)
                    print(f"Succès : {csv_output} créé.")
                    return
        except Exception as e:
            print(f"Erreur : {e}")
    else:
        print(f"Fichier {excel_source} introuvable.")

if __name__ == "__main__":
    fix_co2_data()