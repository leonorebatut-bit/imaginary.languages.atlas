"""Lecture des caractéristiques documentées par une grammaire.

Fichier : data/languages/<id>/documented_features.csv, colonnes :
  feature_id, value, source_id, locator, note, coded_by, coded_on
- `source_id` doit exister dans sources.csv de la même langue ;
- `locator` précise la page, la section ou l'URL d'ancre ;
- `value` est une chaîne ; les listes (inventaires IPA) sont séparées par des espaces.
Une ligne sans source est rejetée : aucune valeur documentée sans référence.
"""
from __future__ import annotations

import csv
from pathlib import Path

from ..schema import FeatureValue, Status

COLUMNS = ["feature_id", "value", "source_id", "locator", "note", "coded_by", "coded_on"]


class DocumentedFeatureError(ValueError):
    pass


def load_documented(path: Path, known_source_ids: set[str]) -> dict[str, FeatureValue]:
    if not path.exists():
        return {}
    out: dict[str, FeatureValue] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for i, row in enumerate(csv.DictReader(fh), start=2):
            fid = (row.get("feature_id") or "").strip()
            if not fid:
                continue
            src = (row.get("source_id") or "").strip()
            if not src:
                raise DocumentedFeatureError(f"{path}:{i}: {fid} sans source")
            if src not in known_source_ids:
                raise DocumentedFeatureError(f"{path}:{i}: source inconnue {src!r}")
            if fid in out:
                raise DocumentedFeatureError(f"{path}:{i}: {fid} en double")
            domain = fid.split(".", 1)[0]
            locator = (row.get("locator") or "").strip()
            out[fid] = FeatureValue(
                feature_id=fid, domain=domain, value=row["value"].strip(), status=Status.DOCUMENTED,
                method="documented:grammar", source_ids=[src],
                examples=[], limits=(row.get("note") or "").strip() or None,
                unit=None,
            )
            if locator:
                out[fid].source_ids = [f"{src}@{locator}"]
    return out
