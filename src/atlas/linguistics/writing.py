"""Systèmes d'écriture, traités comme des objets distincts des langues.

Les valeurs de type (alphabet, abjad, abugida, syllabaire, logographie) et de
sens d'écriture viennent du catalogue (config/catalog.yaml) et ne sont
renseignées que si elles sont documentées ; sinon null.
"""
from __future__ import annotations

from ..schema import FeatureValue, Status, unavailable

METHOD_VERSION = "writing/1"
SCRIPT_TYPES = {"alphabet", "abjad", "abugida", "syllabary", "logography", "featural", "mixed"}


def script_record(script: dict) -> dict:
    stype = script.get("type")
    if stype is not None and stype not in SCRIPT_TYPES:
        raise ValueError(f"type d'écriture inconnu pour {script['id']}: {stype}")
    return {
        "id": script["id"], "name": script["name"], "universe": script.get("universe"),
        "creator": script.get("creator"), "type": stype, "type_note": script.get("type_note"),
        "direction": script.get("direction"), "represents": script.get("represents", []),
        "metadata_status": script.get("metadata_status", "unverified"),
        "sources": script.get("sources", []),
    }


def writing_features(language: dict, scripts: dict[str, dict]) -> list[FeatureValue]:
    ids = [s for s in language.get("scripts", []) if s in scripts]
    # Un lien n'est « documenté » que si la fiche de l'écriture cite au moins une source.
    documented_links = [s for s in ids if language["id"] in scripts[s].get("represents", [])
                        and scripts[s].get("sources")]
    if documented_links:
        return [FeatureValue("writing.scripts", "writing", documented_links, Status.DOCUMENTED, f"{METHOD_VERSION}:catalog",
                             source_ids=[f"script:{s}" for s in documented_links],
                             limits="relation langue-écriture issue du catalogue, métadonnées à vérifier")]
    unsourced = [s for s in ids if s not in documented_links]
    if unsourced:
        return [unavailable("writing.scripts", "writing", METHOD_VERSION,
                            f"écriture mentionnée au catalogue ({', '.join(unsourced)}) mais sans source : non retenue")]
    return [unavailable("writing.scripts", "writing", METHOD_VERSION, "aucune écriture propre documentée")]
