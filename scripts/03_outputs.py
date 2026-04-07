import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def generate_report_outputs():
    # We must specify the subfolder 'data/processed/'
    try:
        returns_path = 'data/processed/final_returns_matrix.csv'
        ci_path = 'data/processed/final_ci_scores.csv'
        
        returns = pd.read_csv(returns_path, index_col=0)
        ci_data = pd.read_csv(ci_path, index_col='ISIN')
    except FileNotFoundError:
        print("Error: The files were not found in data/processed/. Did you run script 02?")
        return

    # Calculate Annualized Stats
    stats = pd.DataFrame(index=returns.columns)
    stats['Ann_Return'] = returns.mean() * 12
    stats['Ann_Vol'] = returns.std() * np.sqrt(12)
    stats['Sharpe'] = stats['Ann_Return'] / stats['Ann_Vol']
    
    # Merge financial stats with Carbon Intensity
    final_results = stats.join(ci_data, how='inner')
    
    # Create the outputs folder if it doesn't exist
    if not os.path.exists('outputs'):
        os.makedirs('outputs')

    # Print summary results to the terminal
    print("\n--- Pacific Universe Summary (2004-2013) ---")
    summary = final_results.describe().loc[['mean', 'std', 'min', 'max']]
    print(summary)
    
    # Save the CSV and the Chart to the outputs folder
    final_results.to_csv('outputs/portfolio_summary_stats.csv')
    
    plt.figure(figsize=(10, 6))
    plt.scatter(final_results['Ann_Vol'], final_results['CI_2013'], alpha=0.5, color='darkblue')
    plt.title('Risk vs Carbon Intensity (Pacific Region)')
    plt.xlabel('Annualized Volatility')
    plt.ylabel('Carbon Intensity (Scope 1 / Revs)')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig('outputs/risk_vs_carbon.png')
    
    print("\nSuccess! Check the 'outputs/' folder for your results.")

if __name__ == "__main__":
    generate_report_outputs()