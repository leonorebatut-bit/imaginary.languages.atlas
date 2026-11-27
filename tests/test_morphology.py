import csv

import pytest

from atlas.linguistics.morphology import affix_positions, morphology_features, parse_example


def load(fixtures_dir):
    with (fixtures_dir / "glossed_known.tsv").open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def test_parse_and_ratio(fixtures_dir):
    feats = {f.feature_id: f for f in morphology_features(load(fixtures_dir), min_words=4)}
    # ka-tomi-s (3) mesu-n (2) s<um>ulat (2) tomi (1) = 8 morphèmes / 4 mots
    assert feats["morphology.morphemes_per_word"].value == 2.0
    # affixes : préfixe ka ; suffixes s, n ; infixe um -> 1 / 4 préfixe, 2 / 4 suffixes
    assert feats["morphology.prefix_share"].value == 0.25
    assert feats["morphology.suffix_share"].value == 0.5
    assert feats["morphology.infix_count"].value == 1
    cats = feats["morphology.categories_marked"].value
    assert cats["number"] == ["PL"] and cats["case"] == ["ACC"] and cats["tense"] == ["PST"]
    assert feats["morphology.morphemes_per_word"].source_ids == ["fix-s01"]


def test_insufficient_sample_is_unavailable(fixtures_dir):
    feats = morphology_features(load(fixtures_dir), min_words=30)
    assert all(f.value is None and f.status.value == "unavailable" for f in feats)


def test_misaligned_example_rejected():
    with pytest.raises(ValueError):
        parse_example("ka-tomi", "PL")
    with pytest.raises(ValueError):
        parse_example("ka-tomi mesu", "PL-house")


def test_person_number_gloss_is_grammatical():
    w = parse_example("tomi-ra", "house-3SG")[0]
    assert affix_positions(w) == {"prefix": 0, "suffix": 1, "infix": 0}
