"""Correspondances projet → WALS (config/feature_mapping.yaml).

Les libellés et valeurs possibles sont validés contre codes.csv : une
correspondance qui ne retrouve pas un libellé WALS fait échouer le chargement.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..config import load_yaml


@dataclass
class Mapping:
    project_feature: str
    wals_id: str
    transform: str
    scale: str
    justification: str
    bins: list[dict] = field(default_factory=list)
    wals_name: str | None = None
    domain: str | None = None
    possible_values: list[str] = field(default_factory=list)
    non_ordinal_labels: list[str] = field(default_factory=list)

    def ordinal_levels(self) -> list[str]:
        return [v for v in self.possible_values if v not in self.non_ordinal_labels]

    def convert(self, value: Any) -> str | None:
        """Convertit une valeur du projet en libellé WALS, ou None si non convertible."""
        if value is None:
            return None
        if self.transform == "label":
            v = str(value).strip()
            return v if v in self.possible_values else None
        if self.transform == "bins":
            try:
                x = float(value)
            except (TypeError, ValueError):
                return None
            for b in self.bins:
                if x >= b["min"] and (b["max"] is None or x <= b["max"]):
                    return b["label"]
            return None
        raise ValueError(f"transformation inconnue : {self.transform}")


def load_mappings(config: dict | None = None) -> list[Mapping]:
    cfg = config or load_yaml("feature_mapping.yaml")
    out = []
    for m in cfg["mappings"]:
        if m["scale"] not in ("nominal", "ordinal"):
            raise ValueError(f"{m['wals_id']}: échelle inconnue {m['scale']}")
        out.append(Mapping(m["project_feature"], m["wals_id"], m["transform"], m["scale"],
                           " ".join(m["justification"].split()), bins=m.get("bins", []),
                           non_ordinal_labels=m.get("non_ordinal_labels", []),
                           domain=m["project_feature"].split(".")[0]))
    ids = [m.wals_id for m in out]
    if len(ids) != len(set(ids)):
        raise ValueError("caractéristique WALS associée deux fois")
    return out


def validate_against_wals(mappings: list[Mapping], wals) -> list[Mapping]:
    """Remplit nom et valeurs possibles depuis WALS ; lève si une valeur ne correspond pas."""
    params = dict(zip(wals.parameters.ID, wals.parameters.Name))
    for m in mappings:
        if m.wals_id not in params:
            raise ValueError(f"{m.wals_id} absent de WALS")
        m.wals_name = params[m.wals_id]
        m.possible_values = wals.code_labels(m.wals_id)
        for b in m.bins:
            if b["label"] not in m.possible_values:
                raise ValueError(f"{m.wals_id}: libellé {b['label']!r} absent de WALS {m.possible_values}")
    return mappings


def mapping_table(mappings: list[Mapping]) -> list[dict]:
    return [{"wals_id": m.wals_id, "wals_name": m.wals_name, "domain": m.domain, "project_feature": m.project_feature,
             "possible_values": m.possible_values, "transform": m.transform, "scale": m.scale,
             "justification": m.justification} for m in mappings]
