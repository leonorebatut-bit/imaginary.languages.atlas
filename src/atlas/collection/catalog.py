"""Lecture et validation du catalogue (config/catalog.yaml)."""
from __future__ import annotations

from ..config import load_yaml

CATEGORIES = {"constructed_fictional", "constructed_external", "fragmentary", "idiolect", "sociolect",
              "transformed_variety", "pseudo_language"}
DOC_LEVELS = {"high", "medium", "low", "fragmentary"}
REQUIRED = ("id", "name", "category", "universe", "creator", "year", "description", "documentation_level",
            "corpus_type", "real_language_reference", "sources", "metadata_status")


def load_catalog(config: dict | None = None) -> dict:
    cat = config or load_yaml("catalog.yaml")
    ids = set()
    for lang in cat["languages"]:
        missing = [k for k in REQUIRED if k not in lang]
        if missing:
            raise ValueError(f"{lang.get('id')}: champs manquants {missing}")
        if lang["category"] not in CATEGORIES:
            raise ValueError(f"{lang['id']}: catégorie inconnue {lang['category']}")
        if lang["documentation_level"] not in DOC_LEVELS:
            raise ValueError(f"{lang['id']}: niveau de documentation inconnu")
        if lang["id"] in ids:
            raise ValueError(f"identifiant en double : {lang['id']}")
        ids.add(lang["id"])
    script_ids = {s["id"] for s in cat.get("scripts", [])}
    for s in cat.get("scripts", []):
        for target in s.get("represents", []):
            if target not in ids:
                raise ValueError(f"écriture {s['id']} : langue inconnue {target}")
    for lang in cat["languages"]:
        for s in lang.get("scripts", []):
            if s not in script_ids:
                raise ValueError(f"{lang['id']}: écriture inconnue {s}")
    return cat
