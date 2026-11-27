"""Typologie générale.

Les étiquettes « isolante », « agglutinante », « fusionnelle »,
« polysynthétique », « analytique », « synthétique » ne sont reprises QUE si
une source les documente (statut `documented`).

En complément, on fournit l'indice de synthèse de Greenberg (1960) et la bande
descriptive correspondante, calculés sur les gloses (morphology.py). C'est un
indicateur, explicitement distingué d'une classification.
"""
from __future__ import annotations

from ..schema import FeatureValue, Status, unavailable

METHOD_VERSION = "typology/1"

TYPOLOGY_FEATURES = ("morphological_type", "analytic_synthetic", "dominant_word_order")

# Bandes de Greenberg (1960) pour l'indice de synthèse M/W.
GREENBERG_BANDS = ((1.0, 2.0, "analytique (1,00-1,99)"),
                   (2.0, 3.0, "synthétique (2,00-2,99)"),
                   (3.0, float("inf"), "polysynthétique (>= 3,00)"))


def greenberg_band(index: float) -> str | None:
    for lo, hi, label in GREENBERG_BANDS:
        if lo <= index < hi:
            return label
    return None


def typology_features(documented: dict[str, FeatureValue], computed: dict[str, FeatureValue]) -> list[FeatureValue]:
    out = []
    for f in TYPOLOGY_FEATURES:
        fid = f"typology.{f}"
        if f == "dominant_word_order" and fid not in documented and "syntax.basic_word_order" in documented:
            src = documented["syntax.basic_word_order"]
            out.append(FeatureValue(fid, "typology", src.value, Status.DOCUMENTED, "documented:via_syntax.basic_word_order",
                                    source_ids=src.source_ids))
            continue
        out.append(documented.get(fid) or unavailable(fid, "typology", METHOD_VERSION, "non documenté"))

    ratio = computed.get("morphology.morphemes_per_word")
    if ratio is not None and ratio.value is not None:
        band = greenberg_band(ratio.value)
        out.append(FeatureValue("typology.synthesis_index_band", "typology", band, Status.COMPUTED,
                                f"{METHOD_VERSION}:greenberg_1960", source_ids=ratio.source_ids,
                                limits="indicateur descriptif calculé sur un échantillon glosé ; ce n'est pas une classification"))
    else:
        out.append(unavailable("typology.synthesis_index_band", "typology", METHOD_VERSION, "indice de synthèse non calculable"))
    return out
