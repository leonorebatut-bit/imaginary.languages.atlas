"""Lecture et validation du catalogue (config/catalog.yaml)."""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from ..config import load_yaml, pipeline_config

CATEGORIES = {"constructed_fictional", "constructed_external", "fragmentary", "idiolect", "sociolect",
              "transformed_variety", "pseudo_language"}
DOC_LEVELS = {"high", "medium", "low", "fragmentary"}
REQUIRED = ("id", "name", "category", "universe", "creator", "year", "description", "documentation_level",
            "corpus_type", "real_language_reference", "sources", "metadata_status")


# Un identifiant sert de nom de dossier : format strict, pour qu'il ne puisse pas
# désigner un chemin hors de data/ (« ../ », « / »).
ID_PATTERN = re.compile(r"^[a-z0-9_]{1,64}$")


def check_url(url: str, allowed_hosts: list[str]) -> None:
    """Refuse toute URL non HTTPS ou dont l'hôte n'est pas dans http.allowed_hosts."""
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname not in allowed_hosts or parts.username or parts.port:
        raise ValueError(f"URL refusée (HTTPS et hôtes de http.allowed_hosts uniquement) : {url}")


def load_catalog(config: dict | None = None) -> dict:
    cat = config or load_yaml("catalog.yaml")
    allowed = pipeline_config()["http"]["allowed_hosts"]
    ids = set()
    for lang in cat["languages"]:
        missing = [k for k in REQUIRED if k not in lang]
        if missing:
            raise ValueError(f"{lang.get('id')}: champs manquants {missing}")
        if not ID_PATTERN.match(str(lang["id"])):
            raise ValueError(f"identifiant invalide (a-z, 0-9, _) : {lang['id']!r}")
        for src in lang["sources"]:
            check_url(src["url"], allowed)
        if lang["category"] not in CATEGORIES:
            raise ValueError(f"{lang['id']}: catégorie inconnue {lang['category']}")
        if lang["documentation_level"] not in DOC_LEVELS:
            raise ValueError(f"{lang['id']}: niveau de documentation inconnu")
        if lang["id"] in ids:
            raise ValueError(f"identifiant en double : {lang['id']}")
        ids.add(lang["id"])
    for s in cat.get("scripts", []):
        if not ID_PATTERN.match(str(s["id"])):
            raise ValueError(f"identifiant d'écriture invalide : {s['id']!r}")
        for src in s.get("sources", []):
            check_url(src["url"], allowed)
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
