import pandas as pd
import numpy as np
import os

def run_financial_analysis():
    # --- PART 1: Carbon Intensity (CI) 2013 ---
    try:
        rev = pd.read_csv('data/processed/Clean_Revenues_Pacific.csv')
        co2 = pd.read_csv('data/processed/Clean_Scope1_Pacific.csv')
        
        # Merge Scope 1 and Revenue on ISIN for the year 2013
        # x suffix = CO2, y suffix = Revenues
        merged = pd.merge(co2[['ISIN', '2013']], rev[['ISIN', '2013']], on='ISIN')
        
        # Formula: Emissions / (Revenue / 1000)
        # Drop companies with zero or negative revenue
        merged = merged[merged['2013_y'] > 0].copy()
        merged['CI_2013'] = merged['2013_x'] / (merged['2013_y'] / 1000)
        
        merged[['ISIN', 'CI_2013']].to_csv('data/processed/final_ci_scores.csv', index=False)
        print(f"CI scores calculated for {len(merged)} assets.")
    except Exception as e:
        print(f"Error in CI calculation: {e}")

    # --- PART 2: Returns & Liquidity Filters (2004-2013) ---
    try:
        prices = pd.read_csv('data/processed/Clean_Prices_Pacific.csv')
        # Reshape to have dates as index and ISIN as columns
        prices = prices.set_index('ISIN').iloc[:, 1:].transpose()
        prices.index = pd.to_datetime(prices.index)
        
        # Select the 10-year estimation window
        returns = prices.loc['2004-01-01':'2013-12-31'].pct_change().dropna(how='all')
        
        # Apply HEC liquidity filters:
        # 1. Less than 50% stale prices (zeros in returns)
        # 2. At least 36 months of data
        valid_assets = []
        for col in returns.columns:
            stale_ratio = (returns[col] == 0).mean()
            obs_count = returns[col].count()
            
            if stale_ratio < 0.5 and obs_count >= 36:
                valid_assets.append(col)
        
        final_matrix = returns[valid_assets]
        final_matrix.to_csv('data/processed/final_returns_matrix.csv')
        print(f"Analysis complete: {len(valid_assets)} assets kept in the final matrix.")
        
    except Exception as e:
        print(f"Error in returns analysis: {e}")

if __name__ == "__main__":
    run_financial_analysis()