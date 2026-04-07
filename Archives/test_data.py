import pandas as pd
import os

def debug_filtering():
    # 1. Vérifier l'univers
    if not os.path.exists("Pacific_Universe.csv"):
        print("❌ Pacific_Universe.csv est manquant !")
        return
    
    uni = pd.read_csv("Pacific_Universe.csv")
    isins = uni['ISIN'].unique()
    print(f"✅ Univers Pacifique chargé : {len(isins)} entreprises.")

    # 2. Tester le fichier CO2
    file_co2 = "DS_CO2_SCOPE_1.csv"
    if os.path.exists(file_co2):
        df_co2 = pd.read_csv(file_co2)
        print(f"📊 Fichier CO2 trouvé. Lignes totales : {len(df_co2)}")
        if len(df_co2) == 0:
            print("⚠️ Attention : Ton fichier CO2 est VIDE (0 données).")
        
        # Tentative de filtrage
        clean_co2 = df_co2[df_co2['ISIN'].isin(isins)]
        print(f"🎯 Après filtrage Pacifique : {len(clean_co2)} entreprises restantes.")
        clean_co2.to_csv("Clean_Scope1_Pacific.csv", index=False)
    else:
        print(f"❌ {file_co2} est introuvable dans le dossier.")

debug_filtering()