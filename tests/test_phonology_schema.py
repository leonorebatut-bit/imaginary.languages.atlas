import pytest

from atlas.linguistics.documented import DocumentedFeatureError, load_documented
from atlas.linguistics.phonology import classify_syllable_template, consonant_manner, phonology_features
from atlas.schema import FeatureValue, Status


@pytest.mark.parametrize("tmpl,expected", [
    ("CV", "Simple"), ("(C)V", "Simple"), ("(C)V(C)", "Moderately complex"), ("CCVC", "Moderately complex"),
    ("CCCV", "Complex"), ("CVCC", "Complex"), ("CVCV", None), ("XV", None),
])
def test_syllable_template(tmpl, expected):
    assert classify_syllable_template(tmpl) == expected


@pytest.mark.parametrize("sym,manner", [("p", "plosive"), ("pʰ", "plosive"), ("tʃ", "affricate"),
                                        ("ŋ", "nasal"), ("ɬ", "lateral_fricative"), ("ʘ", None)])
def test_consonant_manner(sym, manner):
    assert consonant_manner(sym) == manner


def test_no_inventory_from_orthography_alone():
    feats = {f.feature_id: f for f in phonology_features({}, ["a", "b", "c"])}
    assert feats["phonology.consonant_inventory_size"].value is None
    assert feats["phonology.observed_graphemes"].status is Status.OBSERVED


def test_documented_inventory_is_counted():
    inv = FeatureValue("phonology.consonant_inventory", "phonology", "p t k m n s", Status.DOCUMENTED,
                       "documented:grammar", source_ids=["x-s01"])
    feats = {f.feature_id: f for f in phonology_features({"phonology.consonant_inventory": inv}, [])}
    assert feats["phonology.consonant_inventory_size"].value == 6
    assert feats["phonology.consonant_types"].value == {"fricative": 1, "nasal": 2, "plosive": 3}


def test_schema_rejects_fabricated_values():
    with pytest.raises(ValueError):
        FeatureValue("syntax.x", "syntax", "SOV", Status.UNAVAILABLE, "m")
    with pytest.raises(ValueError):
        FeatureValue("syntax.x", "syntax", None, Status.COMPUTED, "m")
    with pytest.raises(ValueError):
        FeatureValue("syntax.x", "syntax", "SOV", Status.DOCUMENTED, "m")  # sans source


def test_documented_loader_requires_known_source(tmp_path):
    p = tmp_path / "documented_features.csv"
    p.write_text("feature_id,value,source_id,locator,note,coded_by,coded_on\nsyntax.basic_word_order,OVS,x-s01,p. 59,,,\n",
                 encoding="utf-8")
    feats = load_documented(p, {"x-s01"})
    assert feats["syntax.basic_word_order"].source_ids == ["x-s01@p. 59"]
    with pytest.raises(DocumentedFeatureError):
        load_documented(p, {"autre"})
    p.write_text("feature_id,value,source_id\nsyntax.basic_word_order,OVS,\n", encoding="utf-8")
    with pytest.raises(DocumentedFeatureError):
        load_documented(p, {"x-s01"})
