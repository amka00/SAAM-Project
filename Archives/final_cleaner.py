import pandas as pd
import os

def clean_strategy():
    # 1. Charger l'univers Pacific (exclut BBVA Argentina automatiquement)
    if not os.path.exists("Pacific_Universe.csv"):
        print("Pacific_Universe.csv introuvable.")
        return
    
    uni = pd.read_csv("Pacific_Universe.csv")
    valid_isins = uni['ISIN'].unique()

    # 2. Filtrage des Revenus (On saute la ligne d'erreur Datastream)
    if os.path.exists("DS_REV_USD_Y.csv"):
        # skiprows=[1] permet d'ignorer l'erreur $$ER: E100
        df_rev = pd.read_csv("DS_REV_USD_Y.csv", skiprows=[1])
        clean_rev = df_rev[df_rev['ISIN'].isin(valid_isins)]
        clean_rev.to_csv("Clean_Revenues_Pacific.csv", index=False)
        print(f"Revenues filtrés : {len(clean_rev)} entreprises (Zone PAC).")

    # 3. Filtrage du Scope 1
    if os.path.exists("DS_CO2_SCOPE_1.csv"):
        df_co2 = pd.read_csv("DS_CO2_SCOPE_1.csv")
        if len(df_co2) == 0:
            print("Attention : Ton fichier CO2 est vide. Tu dois le remplir.")
        else:
            clean_co2 = df_co2[df_co2['ISIN'].isin(valid_isins)]
            clean_co2.to_csv("Clean_Scope1_Pacific.csv", index=False)
            print(f"Scope 1 filtré : {len(clean_co2)} entreprises.")

if __name__ == "__main__":
    clean_strategy()