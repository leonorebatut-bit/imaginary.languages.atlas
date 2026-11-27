"""Exports finaux : language_features.csv / .json, run_manifest.json.

language_features.csv : une ligne par langue ; pour chaque caractéristique,
deux colonnes `<feature_id>__value` et `<feature_id>__status`. Les listes et
dictionnaires sont sérialisés en JSON ; une valeur inconnue vaut null.
language_features.json : enregistrement complet (méthode, sources, exemples,
limites) de chaque caractéristique, plus les métadonnées de la langue.
"""
from __future__ import annotations

import json
import platform
from pathlib import Path

from . import __version__
from .config import pipeline_config, project_path
from .writing_utils import write_csv, write_json

META_COLUMNS = ["id", "name", "category", "universe", "creator", "year", "documentation_level", "metadata_status",
                "corpus_status"]


def _sha_of_raw() -> dict[str, str]:
    out = {}
    raw = project_path("raw")
    for meta in sorted(raw.rglob("*.meta.json")):
        m = json.loads(meta.read_text())
        out[str(meta.relative_to(raw)).removesuffix(".meta.json")] = m.get("sha256")
    return out


def export_all(catalog: dict, metas: list[dict], processed: Path, out: Path) -> None:
    feats = {r["language_id"]: r["features"] for r in json.loads((processed / "features.json").read_text())}
    feature_ids = sorted({f["feature_id"] for fl in feats.values() for f in fl})

    rows, full = [], []
    for meta in metas:
        lid = meta["id"]
        by_id = {f["feature_id"]: f for f in feats.get(lid, [])}
        row = {k: meta.get(k) for k in META_COLUMNS if k != "corpus_status"}
        row["corpus_status"] = meta["corpus"]["status"]
        for fid in feature_ids:
            f = by_id.get(fid)
            row[f"{fid}__value"] = None if f is None else f["value"]
            row[f"{fid}__status"] = "unavailable" if f is None else f["status"]
        rows.append(row)
        full.append({"language": meta, "features": [by_id[k] for k in sorted(by_id)]})

    cols = META_COLUMNS + [f"{fid}__{s}" for fid in feature_ids for s in ("value", "status")]
    write_csv(out / "language_features.csv", rows, cols)
    write_json(out / "language_features.json", full)

    cfg = pipeline_config()
    write_json(out / "run_manifest.json", {
        "pipeline_version": cfg["pipeline_version"], "package_version": __version__,
        "python": platform.python_version(),
        "reference_data": {k: {"version": v["version"], "license": v["license"]} for k, v in cfg["reference_data"].items()},
        "raw_sha256": _sha_of_raw(),
        "n_languages": len(metas),
        "n_scripts": len(catalog.get("scripts", [])),
    })
