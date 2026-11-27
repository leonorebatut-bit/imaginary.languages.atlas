import unicodedata

from atlas.preprocessing.text import clean_corpus, graphemes, sentences, tokenize


def test_clean_removes_comments_blank_lines_and_extra_spaces(fixtures_dir):
    text = clean_corpus((fixtures_dir / "corpus_known.txt").read_text(encoding="utf-8"))
    assert text.splitlines() == ["ka tomi ka tomi.", "ka tomi ka tomi!"]


def test_clean_applies_nfc():
    decomposed = "Quénya"  # e + accent combinant
    assert clean_corpus(decomposed) == unicodedata.normalize("NFC", decomposed)
    assert len(clean_corpus(decomposed)) == 6


def test_tokenize_default_keeps_internal_apostrophe_only():
    assert tokenize("L'homme dit 'oui'.") == ["l'homme", "dit", "oui"]


def test_tokenize_klingon_apostrophe_and_case():
    toks = tokenize("qaStaH nuq? ’ej Qapla'!", apostrophe_is_letter=True, case_sensitive=True)
    assert toks == ["qaStaH", "nuq", "'ej", "Qapla'"]


def test_sentences_split():
    assert sentences("A b. C d! E") == ["A b.", "C d!", "E"]


def test_graphemes_are_clusters_and_exclude_hyphen():
    assert graphemes(["ñá-b"]) == ["ñ", "á", "b"]
