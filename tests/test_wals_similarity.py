import random

import pandas as pd
import pytest

from atlas.comparison.feature_mapping import Mapping, load_mappings, validate_against_wals
from atlas.comparison.similarity import compare_to_all, gower, resolve_weights
from atlas.comparison.wals_loader import load_wals
from atlas.config import load_yaml


def nominal(i):
    return Mapping(f"p.{i}", i, "label", "nominal", "test", possible_values=["x", "y", "z"])


ORD = Mapping("p.o", "O", "label", "ordinal", "test", possible_values=["l1", "l2", "l3", "hors"],
              non_ordinal_labels=["hors"])


def test_wals_loader_and_wide(fixtures_dir):
    w = load_wals(fixtures_dir / "wals_mini")
    wide = w.wide(["1A", "81A"])
    assert wide.loc["aaa", "1A"] == "Average" and wide.loc["aaa", "81A"] == "SOV"
    assert pd.isna(wide.loc["bbb", "81A"])
    assert w.code_labels("1A")[0] == "Small"


def test_real_mapping_config_is_consistent():
    maps = load_mappings()
    assert len({m.wals_id for m in maps}) == len(maps)
    assert all(m.justification for m in maps)


def test_mapping_validation_against_wals(fixtures_dir):
    w = load_wals(fixtures_dir / "wals_mini")
    cfg = {"mappings": [m for m in load_yaml("feature_mapping.yaml")["mappings"] if m["wals_id"] in ("1A", "81A")]}
    maps = validate_against_wals(load_mappings(cfg), w)
    one_a = next(m for m in maps if m.wals_id == "1A")
    assert one_a.convert(22) == "Average" and one_a.convert(34) == "Large" and one_a.convert(5) is None
    order = next(m for m in maps if m.wals_id == "81A")
    assert order.convert("OVS") == "OVS" and order.convert("OSV?") is None and order.convert(None) is None
    bad = {"mappings": [{**cfg["mappings"][0], "wals_id": "999Z"}]}
    with pytest.raises(ValueError):
        validate_against_wals(load_mappings(bad), w)


def test_gower_hand_computed():
    maps = [nominal("N"), ORD]
    assert gower("a", {"N": "x", "O": "l1"}, "b", {"N": "x", "O": "l3"}, maps, {}, 1).score == 0.5
    r = gower("a", {"N": "x", "O": "l1"}, "b", {"N": "x", "O": "l2"}, maps, {}, 1)
    assert r.score == 0.75 and r.matching == ["N"] and r.diverging == ["O"] and r.n_compared == 2
    # libellé hors échelle : traité comme nominal
    assert gower("a", {"O": "hors"}, "b", {"O": "l1"}, maps, {}, 1).score == 0.0


def test_missing_values_excluded_from_denominator():
    maps = [nominal("N1"), nominal("N2"), nominal("N3")]
    r = gower("a", {"N1": "x", "N2": None}, "b", {"N1": "x", "N2": "y", "N3": "z"}, maps, {}, 1)
    assert r.n_compared == 1 and r.score == 1.0


def test_min_comparable_threshold_gives_no_score():
    maps = [nominal("N1"), nominal("N2")]
    r = gower("a", {"N1": "x"}, "b", {"N1": "x"}, maps, {}, min_comparable=2)
    assert r.score is None and r.n_compared == 1


def test_weights_and_zero_weight_exclusion():
    maps = [nominal("N1"), nominal("N2")]
    a, b = {"N1": "x", "N2": "x"}, {"N1": "x", "N2": "y"}
    assert gower("a", a, "b", b, maps, {"N1": 3.0}, 1).score == 0.75
    r = gower("a", a, "b", b, maps, {"N2": 0.0}, 1)
    assert r.n_compared == 1 and r.score == 1.0


def test_scores_bounded_and_reproducible():
    rng = random.Random(0)
    maps = [nominal(f"N{i}") for i in range(6)] + [ORD]
    vals = {m.wals_id: m.possible_values for m in maps}
    for _ in range(300):
        a = {k: rng.choice(v + [None]) for k, v in vals.items()}
        b = {k: rng.choice(v + [None]) for k, v in vals.items()}
        r1, r2 = gower("a", a, "b", b, maps, {}, 1), gower("a", a, "b", b, maps, {}, 1)
        assert r1 == r2
        assert r1.score is None or 0.0 <= r1.score <= 1.0


def test_compare_to_all(fixtures_dir):
    w = load_wals(fixtures_dir / "wals_mini")
    cfg = {"mappings": [m for m in load_yaml("feature_mapping.yaml")["mappings"] if m["wals_id"] in ("1A", "81A")]}
    maps = validate_against_wals(load_mappings(cfg), w)
    wide = w.wide(["1A", "81A"]).astype(object)
    wide = wide.where(wide.notna(), None)
    res = {r.b: r for r in compare_to_all("x", {"1A": "Average", "81A": "SOV"}, wide, maps, {}, 1)}
    assert res["aaa"].score == 1.0 and res["aaa"].n_compared == 2
    assert res["bbb"].score == pytest.approx(0.5)   # Average vs Large : 1 - 2/4
    assert res["ccc"].score == 0.0


def test_weight_profiles():
    cfg = load_yaml("weights.yaml")
    assert resolve_weights(cfg) == {}
    assert resolve_weights(cfg, "no_phonology")["1A"] == 0.0
    with pytest.raises(KeyError):
        resolve_weights(cfg, "inexistant")


def test_group_rows_are_not_languages(fixtures_dir):
    w = load_wals(fixtures_dir / "wals_mini")
    assert "genus-g1" not in set(w.languages.ID) and len(w.languages) == 4
