import pytest

from atlas.linguistics.lexicon import hdd, lexicon_features, mattr, mean_word_length, mtld, top_ngrams, ttr
from atlas.preprocessing.text import clean_corpus, tokenize

CFG = {"mattr_window": 2, "mtld_threshold": 0.72, "hdd_sample": 2, "min_tokens": 4}


def test_known_corpus(fixtures_dir):
    toks = tokenize(clean_corpus((fixtures_dir / "corpus_known.txt").read_text(encoding="utf-8")))
    assert toks == ["ka", "tomi"] * 4
    assert ttr(toks) == 0.25
    assert mean_word_length(toks) == 3.0
    assert top_ngrams(toks, 2, k=1) == [("ka tomi", 4)]


def test_mattr_hand_computed():
    # fenêtres (a,b)=1.0 ; (b,a)=1.0 ; (a,a)=0.5  -> 2.5/3
    assert mattr(list("abaa"), 2) == pytest.approx(2.5 / 3)
    assert mattr(list("ab"), 3) is None


def test_mtld_constant_text():
    # TTR tombe à 0.5 tous les 2 tokens : 5 facteurs pour 10 tokens -> MTLD = 2
    assert mtld(["a"] * 10) == pytest.approx(2.0)


def test_mtld_all_distinct_is_undefined():
    assert mtld(list("abcdef")) is None


def test_hdd_all_distinct_equals_one():
    assert hdd([str(i) for i in range(42)], 42) == pytest.approx(1.0)


def test_hdd_constant_text():
    # un seul type, toujours présent dans l'échantillon -> 1/42
    assert hdd(["a"] * 100, 42) == pytest.approx(1 / 42)


def test_small_corpus_gives_null_not_zero():
    feats = {f.feature_id: f for f in lexicon_features(["a", "b"], CFG)}
    assert feats["lexicon.mattr"].value is None
    assert feats["lexicon.mattr"].status.value == "unavailable"
    assert feats["lexicon.token_count"].value == 2


def test_empty_corpus_all_unavailable():
    assert all(f.value is None for f in lexicon_features([], CFG))
