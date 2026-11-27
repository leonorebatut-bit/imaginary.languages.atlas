"""Cohérence des données publiées pour le site (frontend/public/data/).

Ces fichiers sont produits par l'étape `site_data` du pipeline et versionnés,
car le site statique les lit tels quels.
"""
import json
import math
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[1] / "frontend" / "public" / "data"
FILES = ["languages.json", "scripts.json", "wals_languages.json", "regions.json", "nearest.json",
         "mapping.json", "areas.json", "manifest.json"]


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def site():
    missing = [f for f in FILES if not (DATA / f).exists()]
    if missing:
        pytest.skip(f"données du site absentes : {missing} (lancer scripts/rebuild_all.py)")
    return {f.split(".")[0]: load(f) for f in FILES}


def walk(x):
    if isinstance(x, dict):
        for v in x.values():
            yield from walk(v)
    elif isinstance(x, list):
        for v in x:
            yield from walk(v)
    else:
        yield x


def test_no_nan_or_string_null(site):
    for name, content in site.items():
        for v in walk(content):
            assert not (isinstance(v, float) and math.isnan(v)), name
            assert v not in ("nan", "NaN", "null"), name


def test_scored_flag_follows_threshold(site):
    threshold = site["manifest"]["min_comparable_features"]
    for lang in site["languages"]:
        assert lang["n_wals_features"] == len(lang["wals_profile"])
        assert lang["scored"] == (lang["n_wals_features"] >= threshold)


def test_scores_only_for_scored_languages_and_in_range(site):
    scored = {l["id"] for l in site["languages"] if l["scored"]}
    assert {r["imaginary_id"] for r in site["regions"]} <= scored
    assert set(site["nearest"]) <= scored
    for r in site["regions"]:
        assert 0 <= r["score_genus_weighted"] <= 1
        if r["ci95_low"] is not None:
            assert 0 <= r["ci95_low"] <= r["ci95_high"] <= 1
        assert r["robust"] == (r["n_languages"] >= 10 and r["n_genera"] >= 3)
        for agg in (r.get("feature_agreement") or {}).values():
            assert 0 <= agg["matching"] <= agg["compared"] <= r["n_languages"]
    for pairs in site["nearest"].values():
        scores = [p["score"] for p in pairs]
        assert scores == sorted(scores, reverse=True)
        for p in pairs:
            assert 0 <= p["score"] <= 1
            assert p["n_compared"] >= site["manifest"]["min_comparable_features"]
            assert p["n_same"] + p["n_different"] <= p["n_compared"]


def test_documented_features_have_sources(site):
    for lang in site["languages"]:
        ids = {s["source_id"] for s in lang["sources"]}
        # Un lien langue-écriture renvoie à la fiche de l'écriture, qui porte ses propres sources.
        ids |= {f"script:{s['id']}" for s in site["scripts"] if s["sources"]}
        for f in lang["features"]:
            if f["status"] == "documented":
                assert f["source_ids"], (lang["id"], f["feature_id"])
                assert all(s.split("@")[0] in ids for s in f["source_ids"]), (lang["id"], f["feature_id"])
            if f["status"] == "unavailable":
                assert f["value"] is None


def test_wals_languages_have_coordinates_and_known_areas(site):
    areas = {a["area"] for a in site["areas"]}
    for w in site["wals_languages"]:
        assert -90 <= w["lat"] <= 90 and -180 <= w["lon"] <= 180
        assert w["area"] is None or w["area"] in areas
    assert {r["area"] for r in site["regions"]} <= areas
