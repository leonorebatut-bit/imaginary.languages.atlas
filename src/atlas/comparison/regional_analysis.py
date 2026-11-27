"""Agrégation régionale des scores de proximité.

Régions : aires linguistiques AUTOTYP (config/regions.yaml). Chaque langue WALS
est placée à ses coordonnées WALS et rattachée à une aire :
  1. par Glottocode s'il figure dans le registre AUTOTYP (`glottocode`) ;
  2. sinon à l'aire de la langue AUTOTYP la plus proche si elle est à moins de
     `max_km` (`nearest_neighbour`, distance enregistrée) ;
  3. sinon aucune aire (`unassigned`) : la langue est exclue de l'agrégation.

Agrégation, pour une langue imaginaire et une aire :
- seules les langues WALS ayant un score (assez de traits comparables) comptent ;
- score régional = moyenne des moyennes par genre WALS, pour qu'un genre très
  représenté (ex. bantou) ne domine pas l'aire ; la moyenne simple et la
  médiane sont aussi fournies ;
- dispersion : écart-type, intervalle interquartile, intervalle de confiance à
  95 % par bootstrap sur les genres (graine fixée) ;
- robustesse : `robust = n_languages >= min_languages et n_genera >= min_genera`.
Le résultat est une PROXIMITÉ TYPOLOGIQUE, pas une origine, une parenté ou
une influence.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def assign_areas(wals_languages: pd.DataFrame, register: pd.DataFrame, max_km: float) -> pd.DataFrame:
    reg = register.dropna(subset=["Area"]).copy()
    by_glotto = reg.dropna(subset=["Glottocode"]).drop_duplicates("Glottocode").set_index("Glottocode")["Area"]
    reg_xy = reg.dropna(subset=["Latitude", "Longitude"])
    rlat, rlon = reg_xy["Latitude"].to_numpy(float), reg_xy["Longitude"].to_numpy(float)
    rarea = reg_xy["Area"].to_numpy()

    rows = []
    for _, lang in wals_languages.iterrows():
        g = lang.get("Glottocode")
        if isinstance(g, str) and g in by_glotto.index:
            rows.append((lang["ID"], by_glotto[g], "glottocode", 0.0))
            continue
        if pd.notna(lang["Latitude"]) and pd.notna(lang["Longitude"]) and len(rlat):
            d = haversine_km(lang["Latitude"], lang["Longitude"], rlat, rlon)
            i = int(np.argmin(d))
            if d[i] <= max_km:
                rows.append((lang["ID"], rarea[i], "nearest_neighbour", round(float(d[i]), 1)))
                continue
        rows.append((lang["ID"], None, "unassigned", None))
    return pd.DataFrame(rows, columns=["wals_id", "area", "area_method", "area_distance_km"])


def _genus_weighted_mean(df: pd.DataFrame) -> float:
    return float(df.groupby("genus")["score"].mean().mean())


def aggregate(scores: pd.DataFrame, min_languages: int, min_genera: int, n_boot: int, seed: int) -> pd.DataFrame:
    """`scores` : colonnes imaginary_id, wals_id, area, genus, score, n_compared."""
    rng = np.random.default_rng(seed)
    out = []
    valid = scores.dropna(subset=["score", "area"]).copy()
    valid["genus"] = valid["genus"].fillna("genus_inconnu:" + valid["wals_id"])
    for (lang, area), grp in valid.groupby(["imaginary_id", "area"], sort=True):
        genera = sorted(grp["genus"].unique())
        genus_means = grp.groupby("genus")["score"].mean().reindex(genera).to_numpy()
        if len(genera) > 1:
            boot = rng.choice(genus_means, size=(n_boot, len(genera)), replace=True).mean(axis=1)
            ci_low, ci_high = (round(float(x), 6) for x in np.percentile(boot, [2.5, 97.5]))
        else:
            ci_low = ci_high = None
        q1, q3 = np.percentile(grp["score"], [25, 75])
        out.append({
            "imaginary_id": lang, "area": area,
            "score_genus_weighted": round(_genus_weighted_mean(grp), 6),
            "score_mean": round(float(grp["score"].mean()), 6),
            "score_median": round(float(grp["score"].median()), 6),
            "score_sd": round(float(grp["score"].std(ddof=1)), 6) if len(grp) > 1 else None,
            "score_iqr": round(float(q3 - q1), 6),
            "ci95_low": ci_low, "ci95_high": ci_high,
            "n_languages": int(len(grp)), "n_genera": len(genera),
            "mean_features_compared": round(float(grp["n_compared"].mean()), 3),
            "robust": bool(len(grp) >= min_languages and len(genera) >= min_genera),
        })
    cols = ["imaginary_id", "area", "score_genus_weighted", "score_mean", "score_median", "score_sd", "score_iqr",
            "ci95_low", "ci95_high", "n_languages", "n_genera", "mean_features_compared", "robust"]
    return pd.DataFrame(out, columns=cols)
