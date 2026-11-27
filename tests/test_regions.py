import pandas as pd
import pytest

from atlas.comparison.regional_analysis import aggregate, assign_areas, haversine_km
from atlas.comparison.wals_loader import load_wals


def test_haversine_paris_london():
    assert haversine_km(48.8566, 2.3522, 51.5074, -0.1278) == pytest.approx(343.5, abs=2)


def test_assign_areas(fixtures_dir):
    w = load_wals(fixtures_dir / "wals_mini")
    reg = pd.read_csv(fixtures_dir / "register_mini.csv", dtype={"Glottocode": str})
    a = assign_areas(w.languages, reg, max_km=500).set_index("wals_id")
    assert a.loc["aaa", "area"] == "Europe" and a.loc["aaa", "area_method"] == "glottocode"
    assert a.loc["ccc", "area"] == "African Savannah" and a.loc["ccc", "area_method"] == "nearest_neighbour"
    assert a.loc["ccc", "area_distance_km"] < 100
    assert a.loc["ddd", "area_method"] == "unassigned" and pd.isna(a.loc["ddd", "area"])


def _scores():
    return pd.DataFrame([
        {"imaginary_id": "x", "wals_id": "l1", "area": "A", "genus": "g1", "score": 0.2, "n_compared": 10},
        {"imaginary_id": "x", "wals_id": "l2", "area": "A", "genus": "g1", "score": 0.4, "n_compared": 12},
        {"imaginary_id": "x", "wals_id": "l3", "area": "A", "genus": "g2", "score": 0.9, "n_compared": 8},
        {"imaginary_id": "x", "wals_id": "l4", "area": "B", "genus": "g3", "score": 0.7, "n_compared": 9},
        {"imaginary_id": "x", "wals_id": "l5", "area": "B", "genus": "g3", "score": None, "n_compared": 2},
        {"imaginary_id": "x", "wals_id": "l6", "area": None, "genus": "g4", "score": 1.0, "n_compared": 9},
    ])


def test_genus_weighted_aggregation_and_robustness():
    agg = aggregate(_scores(), min_languages=3, min_genera=2, n_boot=200, seed=1).set_index("area")
    assert set(agg.index) == {"A", "B"}            # langue sans aire exclue
    a = agg.loc["A"]
    assert a.score_genus_weighted == pytest.approx(0.6)  # (0.3 + 0.9) / 2
    assert a.score_mean == pytest.approx(0.5)
    assert a.n_languages == 3 and a.n_genera == 2 and bool(a.robust)
    b = agg.loc["B"]
    assert b.n_languages == 1 and not bool(b.robust)   # score manquant exclu ; trop peu de données
    assert pd.isna(b.ci95_low)


def test_aggregation_reproducible():
    a1 = aggregate(_scores(), 3, 2, 500, seed=7)
    a2 = aggregate(_scores(), 3, 2, 500, seed=7)
    pd.testing.assert_frame_equal(a1, a2)
