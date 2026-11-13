"""Prépare les CSV bar-race à partir du fichier des prénoms Insee (prenoms-2024.parquet).

Sortie : data/prenoms_filles.csv, data/prenoms_garcons.csv
(1 ligne par année, 1 colonne par prénom ayant été au moins 1 fois dans le top N).
Colonnes ordonnées par 1re apparition dans le top -> couleurs variées entre voisins.
"""
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
TOP_N = 10

df = pd.read_parquet(HERE / "data" / "raw" / "prenoms-2024.parquet")
df = df[(df.niveau_geographique == "FRANCE") & df.periode.str.fullmatch(r"\d{4}")].copy()
df["periode"] = df.periode.astype(int)
df = df[~df.prenom.str.startswith("_")]  # exclut _PRENOMS_RARES

for sexe, name in (("2", "filles"), ("1", "garcons")):
    d = df[df.sexe == sexe]
    wide = d.pivot_table(index="periode", columns="prenom", values="valeur", aggfunc="sum").fillna(0)
    top = wide.apply(lambda r: r.nlargest(TOP_N).index.tolist(), axis=1)
    first = {}
    for year, names in top.items():
        for n in names:
            first.setdefault(n, year)
    cols = sorted(first, key=lambda n: (first[n], -wide.loc[first[n], n]))
    out = wide[cols].astype(int)
    out.index.name = "annee"
    out.to_csv(HERE / "data" / f"prenoms_{name}.csv")
    print(f"{name}: {out.shape[0]} années, {out.shape[1]} prénoms -> prenoms_{name}.csv")
