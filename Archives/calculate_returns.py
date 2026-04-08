import pandas as pd
import numpy as np

df = pd.read_csv('data/processed/prices.csv', index_col=0, parse_dates=True)

returns = np.log(df / df.shift(1))

returns.to_csv('data/processed/returns.csv')

print("returns.csv corrigé ✅")