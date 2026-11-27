"""Préparation des données du site (frontend/public/data/).

Tout ce que le site affiche est précalculé ici, à partir des exports du
pipeline : le site n'effectue aucun calcul scientifique, il ne fait que filtrer
et afficher. Fichiers produits :
- languages.json      fiches des langues imaginaires (métadonnées + caractéristiques)
- scripts.json        systèmes d'écriture
- wals_languages.json langues WALS : coordonnées, aire, genre, famille, profil comparé
- regions.json        scores par aire linguistique pour chaque langue imaginaire
- nearest.json        langues WALS les plus proches de chaque langue imaginaire
- mapping.json        correspondances avec WALS
- areas.json          définition des aires : nombre de langues, centre géographique
- land.geojson        terres émergées (Natural Earth, domaine public) pour le fond de carte
- manifest.json       versions et paramètres
"""
from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import pandas as pd

from .writing_utils import write_json

NEAREST_LIMIT = 50


def _nan_to_none(records: list[dict]) -> list[dict]:
    return [{k: (None if isinstance(v, float) and pd.isna(v) else v) for k, v in r.items()} for r in records]


def build_site_data(out: Path, processed: Path, geography: Path, scripts_json: Path, raw: Path, dest: Path,
                    min_comparable: int, languages_dir: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    full = json.loads((out / "language_features.json").read_text(encoding="utf-8"))
    profiles = json.loads((processed / "profiles.json").read_text(encoding="utf-8"))
    langs = []
    for rec in full:
        lang = dict(rec["language"])
        lang["features"] = rec["features"]
        src_path = languages_dir / lang["id"] / "sources.csv"
        with src_path.open(encoding="utf-8", newline="") as fh:
            lang["sources"] = [{k: (None if v == "null" else v) for k, v in r.items()
                                if k in ("source_id", "url", "title", "type", "license", "retrieved_at", "status",
                                         "available_items", "kept_items")} for r in csv.DictReader(fh)]
        lang["wals_profile"] = profiles.get(lang["id"], {})
        lang["n_wals_features"] = len(lang["wals_profile"])
        lang["scored"] = lang["n_wals_features"] >= min_comparable
        langs.append(lang)
    write_json(dest / "languages.json", langs, compact=True)
    shutil.copy2(scripts_json, dest / "scripts.json")
    shutil.copy2(out / "wals_mapping.json", dest / "mapping.json")

    wl = pd.read_csv(processed / "wals_languages.csv", dtype=str)
    wl["Latitude"] = wl["Latitude"].astype(float)
    wl["Longitude"] = wl["Longitude"].astype(float)
    areas = pd.read_csv(geography / "wals_language_areas.csv", dtype={"wals_id": str})
    wide = pd.read_csv(processed / "wals_wide.csv", index_col=0, dtype=str, keep_default_na=False, na_values=[""])
    merged = wl.merge(areas, left_on="ID", right_on="wals_id", how="left")
    points = []
    for r in merged.itertuples():
        prof = {} if r.ID not in wide.index else {k: v for k, v in wide.loc[r.ID].items() if isinstance(v, str)}
        points.append({"id": r.ID, "name": r.Name, "lat": r.Latitude, "lon": r.Longitude, "area": r.area,
                       "area_method": r.area_method, "family": r.Family, "genus": r.Genus,
                       "macroarea": r.Macroarea, "profile": prof})
    write_json(dest / "wals_languages.json", _nan_to_none(points), compact=True)

    area_rows = []
    for area, g in merged.dropna(subset=["area"]).groupby("area"):
        area_rows.append({"area": area, "n_languages": int(len(g)), "lat": round(float(g.Latitude.median()), 3),
                          "lon": round(float(g.Longitude.median()), 3)})
    write_json(dest / "areas.json", area_rows)

    pairs = pd.read_csv(out / "pairwise_similarity.csv", na_values=["null"]).dropna(subset=["score"])
    reg = pd.read_csv(out / "regional_similarity.csv", na_values=["null"])
    regions = _nan_to_none(reg.to_dict(orient="records"))
    # Pour expliquer un score régional : par caractéristique, nombre de langues de l'aire
    # comparées et nombre de langues concordantes.
    area_of = dict(zip(areas.wals_id, areas.area))
    agreement: dict[tuple[str, str], dict[str, dict[str, int]]] = {}
    for r in pairs.itertuples():
        area = area_of.get(r.wals_id)
        if not isinstance(area, str):
            continue
        acc = agreement.setdefault((r.imaginary_id, area), {})
        for fid in json.loads(r.matching):
            a = acc.setdefault(fid, {"compared": 0, "matching": 0})
            a["compared"] += 1
            a["matching"] += 1
        for fid in json.loads(r.diverging):
            acc.setdefault(fid, {"compared": 0, "matching": 0})["compared"] += 1
    for row in regions:
        row["feature_agreement"] = agreement.get((row["imaginary_id"], row["area"]), {})
    write_json(dest / "regions.json", regions, compact=True)

    nearest = {}
    for lid, g in pairs.groupby("imaginary_id"):
        g = g.sort_values(["score", "n_compared", "wals_id"], ascending=[False, False, True]).head(NEAREST_LIMIT)
        rows = []
        for r in g.itertuples():
            rows.append({"wals_id": r.wals_id, "score": r.score, "n_compared": int(r.n_compared),
                         "n_same": int(r.n_same), "n_different": int(r.n_different),
                         "matching": json.loads(r.matching), "diverging": json.loads(r.diverging)})
        nearest[lid] = rows
    write_json(dest / "nearest.json", nearest, compact=True)

    land = raw / "geography" / "ne_110m_land.geojson"
    if land.exists():
        shutil.copy2(land, dest / "land.geojson")

    manifest = json.loads((out / "run_manifest.json").read_text(encoding="utf-8"))
    manifest["min_comparable_features"] = min_comparable
    manifest["nearest_limit"] = NEAREST_LIMIT
    write_json(dest / "manifest.json", manifest)
