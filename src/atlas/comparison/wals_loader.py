"""Chargement de WALS (jeu de données CLDF, CC-BY-4.0).

Les fichiers sont téléchargés une fois dans data/raw/wals/<version>/ puis lus
localement. On lit directement les CSV CLDF avec pandas (pas de dépendance à
pycldf) ; les colonnes attendues sont vérifiées.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ..config import pipeline_config, project_path
from ..http_cache import FetchResult, fetch

log = logging.getLogger(__name__)

REQUIRED_COLUMNS = {
    "languages.csv": {"ID", "Name", "Macroarea", "Latitude", "Longitude", "Glottocode", "Family", "Genus"},
    "parameters.csv": {"ID", "Name"},
    "codes.csv": {"ID", "Parameter_ID", "Name", "Number"},
    "values.csv": {"ID", "Language_ID", "Parameter_ID", "Value", "Code_ID"},
}


@dataclass
class WALS:
    languages: pd.DataFrame
    parameters: pd.DataFrame
    codes: pd.DataFrame
    values: pd.DataFrame
    version: str

    def wide(self, parameter_ids: list[str] | None = None) -> pd.DataFrame:
        """Tableau langue × caractéristique contenant les LIBELLÉS des codes (NaN si non codé)."""
        vals = self.values if parameter_ids is None else self.values[self.values.Parameter_ID.isin(parameter_ids)]
        labelled = vals.merge(self.codes[["ID", "Name"]].rename(columns={"ID": "Code_ID", "Name": "Label"}), on="Code_ID", how="left")
        wide = labelled.pivot_table(index="Language_ID", columns="Parameter_ID", values="Label", aggfunc="first")
        return wide.reindex(columns=parameter_ids) if parameter_ids else wide

    def code_labels(self, parameter_id: str) -> list[str]:
        sub = self.codes[self.codes.Parameter_ID == parameter_id].sort_values("Number")
        return sub["Name"].tolist()


def download_wals(raw_dir: Path | None = None, force: bool = False) -> list[FetchResult]:
    cfg = pipeline_config()["reference_data"]["wals"]
    target = (raw_dir or project_path("raw")) / "wals" / cfg["version"]
    return [fetch(f"{cfg['base_url']}/{name}", target / name, force=force) for name in cfg["files"]]


def load_wals(directory: Path | None = None) -> WALS:
    cfg = pipeline_config()["reference_data"]["wals"]
    d = directory or project_path("raw") / "wals" / cfg["version"]
    frames = {}
    for name, cols in REQUIRED_COLUMNS.items():
        df = pd.read_csv(d / name, dtype=str, keep_default_na=False, na_values=[""])
        missing = cols - set(df.columns)
        if missing:
            raise ValueError(f"{name}: colonnes manquantes {sorted(missing)}")
        frames[name] = df
    langs = frames["languages.csv"]
    langs["Latitude"] = pd.to_numeric(langs["Latitude"])
    langs["Longitude"] = pd.to_numeric(langs["Longitude"])
    # languages.csv contient aussi des lignes de regroupement (family-…, genus-…,
    # subfamily-…) sans coordonnées : elles ne sont pas des langues et sont écartées.
    is_group = langs["ID"].str.match(r"^(family|subfamily|genus)-")
    langs = langs[~is_group & langs["Latitude"].notna()].reset_index(drop=True)
    codes = frames["codes.csv"]
    codes["Number"] = pd.to_numeric(codes["Number"])
    return WALS(langs, frames["parameters.csv"], codes, frames["values.csv"], cfg["version"])
