"""Lecture des caractéristiques documentées par une grammaire.

Fichier : data/languages/<id>/documented_features.csv, colonnes :
  feature_id, value, source_id, locator, evidence, note, coded_by, coded_on
- `source_id` doit exister dans sources.csv de la même langue ;
- `locator` précise la page, la section ou l'URL d'ancre ;
- `evidence` est une citation courte et LITTÉRALE de la source qui justifie la
  valeur. Si le texte de la source est disponible localement, la citation y est
  recherchée (normalisation des espaces, guillemets et casse) : une citation
  introuvable, ou une source dont le texte n'a pas pu être téléchargé, fait
  échouer le chargement. C'est ce qui rend chaque valeur vérifiable. Pour un
  inventaire, la citation doit porter sur l'inventaire lui-même (phrase ou
  ligne du tableau), pas seulement sur la section ;
- `value` est une chaîne ; les listes (inventaires IPA) sont séparées par des espaces.
Une ligne sans source est rejetée : aucune valeur documentée sans référence.
"""
from __future__ import annotations

import csv
from pathlib import Path

from ..collection.html_text import normalize_for_match
from ..schema import FeatureValue, Status

COLUMNS = ["feature_id", "value", "source_id", "locator", "evidence", "note", "coded_by", "coded_on"]


class DocumentedFeatureError(ValueError):
    pass


def load_documented(path: Path, known_source_ids: set[str],
                    source_texts: dict[str, str] | None = None) -> dict[str, FeatureValue]:
    """`source_texts` : texte normalisé (normalize_for_match) de chaque source disponible."""
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
            evidence = (row.get("evidence") or "").strip()
            if source_texts is not None:
                if not evidence:
                    raise DocumentedFeatureError(f"{path}:{i}: {fid} sans citation de preuve")
                text = source_texts.get(src)
                if text is None:
                    # Source non téléchargée (hors ligne, erreur réseau) : la citation ne peut pas être
                    # vérifiée, donc la valeur n'est pas acceptée.
                    raise DocumentedFeatureError(
                        f"{path}:{i}: texte de {src} indisponible, citation invérifiable (relancer la collecte)")
                else:
                    for part in evidence.split(" [...] "):
                        if normalize_for_match(part) not in text:
                            raise DocumentedFeatureError(f"{path}:{i}: citation introuvable dans {src} : {part[:80]!r}")
                    if fid.endswith("_inventory"):
                        # Chaque symbole d'un inventaire relevé dans un tableau doit figurer dans la source.
                        for sym in row["value"].split():
                            if normalize_for_match(sym) not in text:
                                raise DocumentedFeatureError(f"{path}:{i}: symbole {sym!r} absent de {src}")
            if fid in out:
                raise DocumentedFeatureError(f"{path}:{i}: {fid} en double")
            domain = fid.split(".", 1)[0]
            locator = (row.get("locator") or "").strip()
            out[fid] = FeatureValue(
                feature_id=fid, domain=domain, value=row["value"].strip(), status=Status.DOCUMENTED,
                method="documented:grammar", source_ids=[src],
                examples=[f"« {evidence} »"] if evidence else [], limits=(row.get("note") or "").strip() or None,
                unit=None,
            )
            if locator:
                out[fid].source_ids = [f"{src}@{locator}"]
    return out
