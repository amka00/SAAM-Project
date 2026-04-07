import pandas as pd
import numpy as np

def run_analysis():
    # Lecture dans data/processed
    rev = pd.read_csv('data/processed/Clean_Revenues_Pacific.csv')
    co2 = pd.read_csv('data/processed/Clean_Scope1_Pacific.csv')
    
    # Calcul CI 2013
    df_ci = pd.merge(co2[['ISIN', '2013']], rev[['ISIN', '2013']], on='ISIN')
    df_ci = df_ci[df_ci['2013_y'] > 0].copy()
    df_ci['CI_2013'] = df_ci['2013_x'] / (df_ci['2013_y'] / 1000)
    df_ci[['ISIN', 'CI_2013']].to_csv('data/processed/final_ci_scores.csv', index=False)

    # Rendements 2004-2013
    prices = pd.read_csv('data/processed/Clean_Prices_Pacific.csv')
    prices = prices.set_index('ISIN').iloc[:, 1:].transpose()
    prices.index = pd.to_datetime(prices.index)
    
    returns = prices.loc['2004-01-01':'2013-12-31'].pct_change().dropna(how='all')
    
    # Filtres liquidité
    keep = [c for c in returns.columns if (returns[c]==0).mean() < 0.5 and returns[c].count() >= 36]
    returns[keep].to_csv('data/processed/final_returns_matrix.csv')
    print("Analyse terminée. Matrice générée dans data/processed/")

if __name__ == "__main__":
    run_analysis()