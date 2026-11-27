"""API FastAPI en lecture seule sur les exports du pipeline (outputs/).

Lancement local : uvicorn backend.api.main:app --reload
Le site peut aussi lire directement les JSON statiques ; l'API sert au travail
local, aux tests et à un éventuel déploiement.
"""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

OUTPUTS = Path(os.environ.get("ATLAS_OUTPUTS", Path(__file__).resolve().parents[2] / "outputs"))

app = FastAPI(title="Imaginary Languages Atlas API", version="0.1.0")


def _json(name: str):
    p = OUTPUTS / name
    if not p.exists():
        raise HTTPException(503, f"{name} absent : lancer scripts/rebuild_all.py")
    return json.loads(p.read_text(encoding="utf-8"))


def _csv(name: str) -> list[dict]:
    p = OUTPUTS / name
    if not p.exists():
        raise HTTPException(503, f"{name} absent : lancer scripts/rebuild_all.py")
    with p.open(encoding="utf-8", newline="") as fh:
        return [{k: (None if v == "null" else v) for k, v in r.items()} for r in csv.DictReader(fh)]


@app.get("/api/health")
def health():
    return {"status": "ok", "outputs": str(OUTPUTS)}


@app.get("/api/languages")
def languages(category: str | None = None, universe: str | None = None):
    out = [r["language"] for r in _json("language_features.json")]
    if category:
        out = [l for l in out if l["category"] == category]
    if universe:
        out = [l for l in out if universe.lower() in (l.get("universe") or "").lower()]
    return out


@app.get("/api/languages/{language_id}")
def language(language_id: str):
    for r in _json("language_features.json"):
        if r["language"]["id"] == language_id:
            return r
    raise HTTPException(404, f"langue inconnue : {language_id}")


@app.get("/api/languages/{language_id}/regions")
def regions(language_id: str, robust_only: bool = False):
    rows = [r for r in _csv("regional_similarity.csv") if r["imaginary_id"] == language_id]
    if robust_only:
        rows = [r for r in rows if r["robust"] == "True"]
    return rows


@app.get("/api/languages/{language_id}/nearest")
def nearest(language_id: str, limit: int = Query(20, ge=1, le=200)):
    rows = [r for r in _csv("pairwise_similarity.csv") if r["imaginary_id"] == language_id and r["score"] is not None]
    rows.sort(key=lambda r: (-float(r["score"]), -int(r["n_compared"]), r["wals_id"]))
    return rows[:limit]


@app.get("/api/wals/mapping")
def wals_mapping():
    return _json("wals_mapping.json")
