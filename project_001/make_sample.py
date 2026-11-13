import numpy as np, pandas as pd
rng = np.random.default_rng(1)
names = ["Alpha","Bravo","Charlie","Delta","Echo","Foxtrot","Golf","Hotel","India","Juliet"]
years = list(range(2010, 2025))
start = rng.uniform(50, 300, len(names)); growth = rng.uniform(0.04, 0.22, len(names))
rows = [start * (1 + growth) ** i * rng.uniform(0.9, 1.1, len(names)) for i in range(len(years))]
pd.DataFrame(rows, index=years, columns=names).round(0).to_csv("data/sample.csv", index_label="year")
