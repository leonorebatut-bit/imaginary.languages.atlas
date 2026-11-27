"""Similarité typologique pondérée de Gower (1971).

Pour deux profils a et b (libellés WALS par caractéristique) :

    S(a, b) = Σ_k w_k · δ_k · s_k  /  Σ_k w_k · δ_k

- δ_k = 1 si la caractéristique k est renseignée pour a ET b et w_k > 0, sinon 0
  (les données manquantes sont exclues du dénominateur) ;
- s_k = 1 si les valeurs sont identiques, 0 sinon (variable nominale) ;
- s_k = 1 - |r_a - r_b| / (K - 1) pour une variable ordinale à K niveaux
  (les libellés hors échelle, ex. 49A « Exclusively borderline », sont nominaux).

S est donc dans [0, 1]. Si moins de `min_comparable` caractéristiques sont
comparables, le score vaut None : aucun score n'est attribué.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .feature_mapping import Mapping


@dataclass
class PairResult:
    a: str
    b: str
    n_compared: int
    n_same: int
    n_different: int
    score: float | None
    matching: list[str] = field(default_factory=list)
    diverging: list[str] = field(default_factory=list)
    partial: dict[str, float] = field(default_factory=dict)


def _is_missing(v) -> bool:
    return v is None or (isinstance(v, float) and pd.isna(v))


def feature_similarity(m: Mapping, va: str, vb: str) -> float:
    if va == vb:
        return 1.0
    if m.scale == "ordinal":
        levels = m.ordinal_levels()
        if va in levels and vb in levels and len(levels) > 1:
            return 1.0 - abs(levels.index(va) - levels.index(vb)) / (len(levels) - 1)
    return 0.0


def gower(a_id: str, a: dict, b_id: str, b: dict, mappings: list[Mapping], weights: dict[str, float],
          min_comparable: int) -> PairResult:
    num = den = 0.0
    same = diff = n = 0
    matching, diverging, partial = [], [], {}
    for m in mappings:
        w = float(weights.get(m.wals_id, 1.0))
        va, vb = a.get(m.wals_id), b.get(m.wals_id)
        if w <= 0 or _is_missing(va) or _is_missing(vb):
            continue
        s = feature_similarity(m, va, vb)
        num += w * s
        den += w
        n += 1
        partial[m.wals_id] = round(s, 6)
        if s == 1.0:
            same += 1
            matching.append(m.wals_id)
        else:
            diff += 1
            diverging.append(m.wals_id)
    score = round(num / den, 6) if n >= min_comparable and den > 0 else None
    return PairResult(a_id, b_id, n, same, diff, score, matching, diverging, partial)


def compare_to_all(a_id: str, profile: dict, wals_wide: pd.DataFrame, mappings: list[Mapping],
                   weights: dict[str, float], min_comparable: int) -> list[PairResult]:
    """Compare un profil à chaque langue de WALS (lignes de `wals_wide`, colonnes = ids WALS)."""
    records = wals_wide.to_dict(orient="index")
    return [gower(a_id, profile, lid, row, mappings, weights, min_comparable) for lid, row in records.items()]


def resolve_weights(weights_cfg: dict, profile: str | None = None) -> dict[str, float]:
    name = profile or weights_cfg.get("default_profile", "equal")
    if name not in weights_cfg["profiles"]:
        raise KeyError(f"profil de poids inconnu : {name}")
    return dict(weights_cfg["profiles"][name] or {})
