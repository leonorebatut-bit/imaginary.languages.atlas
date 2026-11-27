"""Tests d'intégration sur les fichiers réellement versionnés.

Ils vérifient que les trois façons de lire les résultats (exports outputs/, API,
données du site) disent la même chose, et que la documentation générée est à jour.
Ils ne relancent pas le pipeline (qui demande le réseau) : ils contrôlent la
cohérence de la dernière exécution versionnée.
"""
import importlib.util
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from atlas.collection.catalog import load_catalog
from backend.api import main

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
SITE = ROOT / "frontend" / "public" / "data"

pytestmark = pytest.mark.skipif(not (OUT / "language_features.json").exists() or not (SITE / "languages.json").exists(),
                                reason="exports absents : lancer scripts/rebuild_all.py")


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def api():
    with pytest.MonkeyPatch.context() as mp:  # chemin restauré après ces tests
        mp.setattr(main, "OUTPUTS", OUT)
        yield TestClient(main.app)


@pytest.fixture(scope="module")
def site():
    return {n: load(SITE / f"{n}.json") for n in ("languages", "regions", "nearest", "manifest", "mapping")}


def test_catalog_outputs_site_and_api_list_the_same_languages(api, site):
    catalog = {l["id"] for l in load_catalog()["languages"]}
    assert {l["id"] for l in api.get("/api/languages").json()} == catalog
    assert {l["id"] for l in site["languages"]} == catalog
    for lid in catalog:
        d = ROOT / "data" / "languages" / lid
        assert (d / "metadata.json").exists() and (d / "sources.csv").exists(), lid


def test_same_run_for_outputs_and_site(site):
    run = load(OUT / "run_manifest.json")
    assert site["manifest"]["raw_sha256"] == run["raw_sha256"]
    # Tout ce que le site reprend du manifeste d'exécution doit être identique.
    for key, value in run.items():
        assert site["manifest"].get(key) == value, key


def test_mappings_identical_everywhere(api, site):
    exported = load(OUT / "wals_mapping.json")
    assert site["mapping"] == exported
    assert api.get("/api/wals/mapping").json() == exported


def test_api_regions_match_site(api, site):
    for lang in (l for l in site["languages"] if l["scored"]):
        from_api = {r["area"]: float(r["score_genus_weighted"]) for r in api.get(f"/api/languages/{lang['id']}/regions").json()}
        from_site = {r["area"]: r["score_genus_weighted"] for r in site["regions"] if r["imaginary_id"] == lang["id"]}
        assert from_api.keys() == from_site.keys(), lang["id"]
        for area, score in from_site.items():
            assert from_api[area] == pytest.approx(score, abs=1e-6), (lang["id"], area)


def test_api_nearest_match_site(api, site):
    scored = {l["id"] for l in site["languages"] if l["scored"]}
    with_api_results = {l for l in scored if api.get(f"/api/languages/{l}/nearest").json()}
    assert set(site["nearest"]) == with_api_results == scored
    for lid, pairs in site["nearest"].items():
        top = api.get(f"/api/languages/{lid}/nearest", params={"limit": 10}).json()
        assert [p["wals_id"] for p in top] == [p["wals_id"] for p in pairs[:10]], lid
        assert [float(p["score"]) for p in top] == pytest.approx([p["score"] for p in pairs[:10]], abs=1e-6)


def test_unscored_languages_have_no_score_anywhere(api, site):
    for lang in (l for l in site["languages"] if not l["scored"]):
        assert api.get(f"/api/languages/{lang['id']}/regions").json() == []
        assert api.get(f"/api/languages/{lang['id']}/nearest").json() == []
        assert lang["id"] not in site["nearest"]


def test_results_doc_is_up_to_date():
    spec = importlib.util.spec_from_file_location("make_results", ROOT / "scripts" / "make_results.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert (ROOT / "docs" / "results.md").read_text(encoding="utf-8") == mod.render(), \
        "docs/results.md n'est plus à jour : lancer python scripts/make_results.py"
