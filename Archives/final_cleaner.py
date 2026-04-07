import pandas as pd
import os

def clean_pacific_strategy():
    # 1. Charger l'univers Pacifique (Source de vérité)
    if not os.path.exists("Pacific_Universe.csv"):
        print("Erreur : Pacific_Universe.csv introuvable.")
        return
    
    uni = pd.read_csv("Pacific_Universe.csv")
    valid_isins = uni['ISIN'].unique()
    print(f"Univers Pacifique chargé : {len(valid_isins)} entreprises.")

    # Liste des fichiers à traiter
    files = [
        ("DS_REV_USD_Y.csv", "Clean_Revenues_Pacific.csv"),
        ("DS_CO2_SCOPE_1.csv", "Clean_Scope1_Pacific.csv")
    ]

    for source, output in files:
        if os.path.exists(source):
            try:
                # On saute la ligne 1 qui contient l'erreur $$ER: E100
                df = pd.read_csv(source, skiprows=[1])
                
                # Filtrage strict par ISIN pour exclure BBVA (Argentine)
                df_filtered = df[df['ISIN'].isin(valid_isins)]
                
                if len(df_filtered) > 0:
                    df_filtered.to_csv(output, index=False)
                    print(f"Succès : {output} créé ({len(df_filtered)} entreprises).")
                else:
                    print(f"Attention : {source} ne contient aucune donnée pour la zone PAC.")
            except Exception as e:
                print(f"Erreur sur {source} : {e}")
        else:
            print(f"Fichier {source} non trouvé.")

if __name__ == "__main__":
    clean_pacific_strategy()