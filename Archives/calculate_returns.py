import pandas as pd
import numpy as np

# Charger les données
df = pd.read_csv('data/processed/Clean_Prices_Pacific.csv')

# Garder les colonnes d'identité
id_cols = ['NAME', 'ISIN']

# Colonnes de prix (toutes les dates)
price_cols = df.columns.drop(id_cols)

# Calcul des log returns (axe horizontal)
log_returns = np.log(df[price_cols] / df[price_cols].shift(axis=1))

# Supprimer la première colonne (NaN car pas de t-1)
log_returns = log_returns.iloc[:, 1:]

# Recombiner avec les identifiants
df_final = pd.concat([df[id_cols], log_returns], axis=1)

# Export
df_final.to_csv('data/processed/returns_pacific.csv', index=False)

print("returns_pacific.csv créé avec succès ✅")