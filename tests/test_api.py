import pytest
from fastapi.testclient import TestClient

from atlas.writing_utils import write_csv, write_json
from backend.api import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    write_json(tmp_path / "language_features.json", [
        {"language": {"id": "klingon", "category": "constructed_fictional", "universe": "Star Trek"}, "features": []},
        {"language": {"id": "yoda", "category": "idiolect", "universe": "Star Wars"}, "features": []}])
    cols = ["imaginary_id", "area", "score_genus_weighted", "n_languages", "robust"]
    write_csv(tmp_path / "regional_similarity.csv", [
        {"imaginary_id": "klingon", "area": "Europe", "score_genus_weighted": 0.6, "n_languages": 12, "robust": True},
        {"imaginary_id": "klingon", "area": "Oceania", "score_genus_weighted": 0.9, "n_languages": 2, "robust": False}], cols)
    write_csv(tmp_path / "pairwise_similarity.csv", [
        {"imaginary_id": "klingon", "wals_id": "a", "n_compared": 9, "score": 0.5},
        {"imaginary_id": "klingon", "wals_id": "b", "n_compared": 9, "score": 0.8},
        {"imaginary_id": "klingon", "wals_id": "c", "n_compared": 3, "score": None}],
        ["imaginary_id", "wals_id", "n_compared", "score"])
    write_json(tmp_path / "wals_mapping.json", [{"wals_id": "81A"}])
    monkeypatch.setattr(main, "OUTPUTS", tmp_path)
    return TestClient(main.app)


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_languages_and_filters(client):
    assert len(client.get("/api/languages").json()) == 2
    assert [l["id"] for l in client.get("/api/languages", params={"category": "idiolect"}).json()] == ["yoda"]
    assert [l["id"] for l in client.get("/api/languages", params={"universe": "trek"}).json()] == ["klingon"]


def test_language_detail_and_404(client):
    assert client.get("/api/languages/klingon").json()["language"]["id"] == "klingon"
    assert client.get("/api/languages/inconnue").status_code == 404


def test_regions_robust_filter(client):
    assert len(client.get("/api/languages/klingon/regions").json()) == 2
    robust = client.get("/api/languages/klingon/regions", params={"robust_only": True}).json()
    assert [r["area"] for r in robust] == ["Europe"]


def test_nearest_excludes_unscored(client):
    assert [r["wals_id"] for r in client.get("/api/languages/klingon/nearest").json()] == ["b", "a"]


def test_missing_outputs_503(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "OUTPUTS", tmp_path / "vide")
    assert TestClient(main.app).get("/api/languages").status_code == 503
