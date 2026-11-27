"""Format homogène d'une caractéristique linguistique.

Chaque valeur produite par le projet est un `FeatureValue`. Une valeur inconnue
vaut `None` (exporté en `null`) avec le statut `unavailable` : elle n'est jamais
remplacée par une valeur arbitraire.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Status(str, Enum):
    DOCUMENTED = "documented"    # tiré d'une grammaire ou d'une description publiée
    OBSERVED = "observed"        # constaté directement dans le corpus
    COMPUTED = "computed"        # calculé par une fonction du projet
    UNAVAILABLE = "unavailable"  # non disponible : value = None


DOMAINS = ("phonology", "morphology", "syntax", "lexicon", "typology", "writing")


@dataclass
class FeatureValue:
    feature_id: str
    domain: str
    value: Any
    status: Status
    method: str
    unit: str | None = None
    source_ids: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    limits: str | None = None

    def __post_init__(self) -> None:
        if self.domain not in DOMAINS:
            raise ValueError(f"domaine inconnu : {self.domain}")
        if not isinstance(self.status, Status):
            self.status = Status(self.status)
        if self.status is Status.UNAVAILABLE and self.value is not None:
            raise ValueError(f"{self.feature_id}: une valeur indisponible doit valoir None")
        if self.status is not Status.UNAVAILABLE and self.value is None:
            raise ValueError(f"{self.feature_id}: valeur None avec le statut {self.status.value}")
        if self.status is Status.DOCUMENTED and not self.source_ids:
            raise ValueError(f"{self.feature_id}: une valeur documentée exige une source")

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


def unavailable(feature_id: str, domain: str, method: str, reason: str, unit: str | None = None) -> FeatureValue:
    return FeatureValue(feature_id, domain, None, Status.UNAVAILABLE, method, unit=unit, limits=reason)
