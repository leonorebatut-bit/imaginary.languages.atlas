"""Chargement de la configuration centrale (dossier config/)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"


def load_yaml(name: str, config_dir: Path | None = None) -> dict[str, Any]:
    path = (config_dir or CONFIG_DIR) / name
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@lru_cache(maxsize=None)
def pipeline_config() -> dict[str, Any]:
    return load_yaml("pipeline.yaml")


def project_path(key: str) -> Path:
    """Chemin absolu d'une entrée de `paths` dans pipeline.yaml."""
    return PROJECT_ROOT / pipeline_config()["paths"][key]
