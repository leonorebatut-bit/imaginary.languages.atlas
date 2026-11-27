import pytest

from atlas.collection.html_text import html_sections, normalize_for_match, source_text
from atlas.comparison.feature_mapping import load_mappings
from atlas.config import load_yaml
from atlas.linguistics.documented import DocumentedFeatureError, load_documented
from atlas.linguistics.syntax import syntax_features
from atlas.schema import FeatureValue, Status

HTML = """<html><body><div id="mw-content-text"><div class="mw-parser-output">
<p>Intro du texte.</p><h2>Phonology</h2><p>Langue X has twenty consonants and “five” vowels.</p>
<table><tr><th>Nasal</th><td>m</td><td>ŋ</td></tr></table><sup>[1]</sup>
<h2>Word order</h2><p>The basic order is object–verb–subject.</p></div></div></body></html>"""

HEADER = "feature_id,value,source_id,locator,evidence,note,coded_by,coded_on\n"


def test_html_sections_and_tables(tmp_path):
    secs = dict(html_sections(HTML))
    assert "Phonology" in secs and "Nasal | m | ŋ" in secs["Phonology"]
    p = tmp_path / "page"
    p.write_text(HTML, encoding="utf-8")
    assert "[1]" not in source_text(p)


def test_normalization_is_tolerant():
    assert normalize_for_match("“Five”  VOWELS – ok") == normalize_for_match('"five" vowels - ok')


def _texts(tmp_path):
    p = tmp_path / "page"
    p.write_text(HTML, encoding="utf-8")
    return {"x-s01": normalize_for_match(source_text(p))}


def test_evidence_found(tmp_path):
    f = tmp_path / "d.csv"
    f.write_text(HEADER + 'phonology.consonant_inventory_size,20,x-s01,§ Phonology,"twenty consonants and ""five"" vowels",,,\n'
                 'syntax.basic_word_order,OVS,x-s01,§ Word order,The basic order [...] object-verb-subject,,,\n', encoding="utf-8")
    d = load_documented(f, {"x-s01"}, _texts(tmp_path))
    assert d["syntax.basic_word_order"].value == "OVS"
    assert d["syntax.basic_word_order"].examples[0].startswith("« The basic order")


def test_evidence_not_found_fails(tmp_path):
    f = tmp_path / "d.csv"
    f.write_text(HEADER + "phonology.consonant_inventory_size,21,x-s01,,twenty-one consonants,,,\n", encoding="utf-8")
    with pytest.raises(DocumentedFeatureError, match="introuvable"):
        load_documented(f, {"x-s01"}, _texts(tmp_path))


def test_missing_evidence_fails(tmp_path):
    f = tmp_path / "d.csv"
    f.write_text(HEADER + "syntax.basic_word_order,OVS,x-s01,,,,,\n", encoding="utf-8")
    with pytest.raises(DocumentedFeatureError, match="sans citation"):
        load_documented(f, {"x-s01"}, _texts(tmp_path))


def test_inventory_symbols_checked(tmp_path):
    f = tmp_path / "d.csv"
    f.write_text(HEADER + "phonology.consonant_inventory,m ŋ ʘ,x-s01,,Nasal,,,\n", encoding="utf-8")
    with pytest.raises(DocumentedFeatureError, match="symbole"):
        load_documented(f, {"x-s01"}, _texts(tmp_path))


def test_object_verb_derived_but_not_subject_verb():
    basic = FeatureValue("syntax.basic_word_order", "syntax", "OVS", Status.DOCUMENTED, "documented:grammar",
                         source_ids=["x-s01"])
    feats = {f.feature_id: f for f in syntax_features({"syntax.basic_word_order": basic})}
    assert feats["syntax.object_verb_order"].value == "OV"
    assert feats["syntax.object_verb_order"].status is Status.COMPUTED
    assert feats["syntax.subject_verb_order"].value is None
    nodom = FeatureValue("syntax.basic_word_order", "syntax", "No dominant order", Status.DOCUMENTED,
                         "documented:grammar", source_ids=["x-s01"])
    assert {f.feature_id: f for f in syntax_features({"syntax.basic_word_order": nodom})}["syntax.object_verb_order"].value is None


def test_range_conversion():
    cfg = {"mappings": [m for m in load_yaml("feature_mapping.yaml")["mappings"] if m["wals_id"] == "1A"]}
    m = load_mappings(cfg)[0]
    assert m.convert("22-24") == "Average"       # les deux bornes dans la même classe
    assert m.convert("17-20") is None            # à cheval sur deux classes : pas de valeur
    assert m.convert("21") == "Average"


def test_real_documented_files_are_valid():
    """Tous les fichiers documented_features.csv du dépôt se chargent et leurs valeurs WALS sont convertibles."""
    from atlas.collection.collect import read_sources
    from atlas.config import project_path
    mappings = {m.project_feature: m for m in load_mappings()}
    labels = {m["wals_id"]: None for m in load_yaml("feature_mapping.yaml")["mappings"]}
    assert labels
    n = 0
    for ldir in sorted(project_path("languages").iterdir()):
        path = ldir / "documented_features.csv"
        if not path.exists():
            continue
        docs = load_documented(path, {r["source_id"] for r in read_sources(ldir)})
        for fid, f in docs.items():
            n += 1
            m = mappings.get(fid)
            if m is not None and m.transform == "label":
                assert f.value in _wals_labels(m.wals_id), (ldir.name, fid, f.value)
    assert n >= 70


def _wals_labels(wals_id):
    import csv
    from atlas.config import project_path, pipeline_config
    v = pipeline_config()["reference_data"]["wals"]["version"]
    path = project_path("raw") / "wals" / v / "codes.csv"
    if not path.exists():
        pytest.skip("WALS absent du cache local : lancer scripts/rebuild_all.py")
    with path.open(encoding="utf-8") as fh:
        return {r["Name"] for r in csv.DictReader(fh) if r["Parameter_ID"] == wals_id}


def test_unavailable_source_text_fails(tmp_path):
    # Une source connue mais non téléchargée : la citation ne peut pas être vérifiée.
    f = tmp_path / "d.csv"
    f.write_text(HEADER + "syntax.basic_word_order,OVS,x-s02,,The basic order,,,\n", encoding="utf-8")
    with pytest.raises(DocumentedFeatureError, match="indisponible"):
        load_documented(f, {"x-s01", "x-s02"}, _texts(tmp_path))
