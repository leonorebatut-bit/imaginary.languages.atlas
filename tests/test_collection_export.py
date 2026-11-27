import bz2
import csv
import json

from atlas.collection.catalog import CATEGORIES, load_catalog
from atlas.collection.collect import collect_all, is_redistributable, sample_sentences
from atlas.export import export_all
from atlas.http_cache import FetchResult
from atlas.writing_utils import write_csv, write_json


def fake_fetcher_factory(tmp_path):
    tsv = tmp_path / "ok_sentences.tsv.bz2"
    tsv.write_bytes(bz2.compress("1\ttst\tka tomi.\n2\ttst\tmesu ka.\n".encode()))

    def fetcher(url, dest, **_):
        if "fail" in url:
            return FetchResult(url, None, False, False, 503, None, None, "HTTP 503")
        return FetchResult(url, str(tsv), True, False, 200, "abc", "2026-11-27T00:00:00+00:00")
    return fetcher


def lang(id_, sources):
    return {"id": id_, "name": id_, "category": "constructed_fictional", "universe": "test", "creator": None, "year": None,
            "description": "test", "documentation_level": "low", "corpus_type": "test", "real_language_reference": None,
            "metadata_status": "unverified", "scripts": [], "sources": sources}


def test_collection_logs_errors_and_continues(tmp_path):
    cat = {"languages": [
        lang("libre", [{"url": "https://x/ok_sentences.tsv.bz2", "type": "sentence_corpus", "license": "CC BY 2.0 FR"},
                       {"url": "https://x/fail", "type": "encyclopedia", "license": "CC BY-SA 4.0"}]),
        lang("protege", [{"url": "https://x/ok_sentences.tsv.bz2", "type": "sentence_corpus", "license": "All rights reserved"}]),
        lang("vide", [{"url": "https://x/fail", "type": "encyclopedia", "license": None}]),
    ]}
    errors = tmp_path / "errors.csv"
    metas = {m["id"]: m for m in collect_all(cat, tmp_path / "langs", tmp_path / "raw", errors, fake_fetcher_factory(tmp_path))}
    assert len(metas) == 3
    assert metas["libre"]["corpus"] == {"status": "available", "file": "corpus.txt", "lines": 2, "redistributable": True}
    assert (tmp_path / "langs/libre/corpus.txt").read_text(encoding="utf-8") == "ka tomi.\nmesu ka.\n"
    # licence non libre : corpus en local seulement (fichier ignoré par git)
    assert metas["protege"]["corpus"]["file"] == "corpus_local.txt"
    assert not (tmp_path / "langs/protege/corpus.txt").exists()
    assert metas["vide"]["corpus"]["status"] == "absent" and "aucune source" in metas["vide"]["corpus"]["justification"]
    with errors.open(encoding="utf-8") as fh:
        errs = list(csv.DictReader(fh))
    assert [e["language_id"] for e in errs] == ["libre", "vide"]
    with (tmp_path / "langs/libre/corpus_manifest.csv").open(encoding="utf-8") as fh:
        assert [r["origin_id"] for r in csv.DictReader(fh)] == ["tatoeba:1", "tatoeba:2"]


def test_license_rules():
    assert is_redistributable("CC BY 2.0 FR") and is_redistributable("CC BY-SA 4.0") and is_redistributable("CC0")
    assert not is_redistributable(None) and not is_redistributable("All rights reserved")


def test_sampling_is_deterministic():
    s = [(str(i), f"s{i}") for i in range(100)]
    a, b = sample_sentences(s, 10, 42), sample_sentences(s, 10, 42)
    assert a == b and len(a) == 10 and a == sorted(a, key=lambda x: int(x[0]))


def test_real_catalog():
    cat = load_catalog()
    assert len(cat["languages"]) == 30
    assert {l["category"] for l in cat["languages"]} <= CATEGORIES
    assert all(l["metadata_status"] == "unverified" for l in cat["languages"])
    scripts = {s["id"] for s in cat["scripts"]}
    assert {"tengwar", "aurebesh", "piqad"} <= scripts
    assert not scripts & {l["id"] for l in cat["languages"]}   # écritures ≠ langues


def test_write_csv_null_and_determinism(tmp_path):
    rows = [{"a": None, "b": [1, 2]}, {"a": "x", "b": {"k": 1}}]
    write_csv(tmp_path / "1.csv", rows, ["a", "b"])
    write_csv(tmp_path / "2.csv", rows, ["a", "b"])
    assert (tmp_path / "1.csv").read_bytes() == (tmp_path / "2.csv").read_bytes()
    assert (tmp_path / "1.csv").read_text().splitlines()[1] == 'null,"[1, 2]"'


def test_export_one_row_per_language(tmp_path, monkeypatch):
    feats = [{"language_id": "l1", "features": [
        {"feature_id": "lexicon.ttr", "domain": "lexicon", "value": 0.5, "status": "computed", "method": "m",
         "unit": None, "source_ids": [], "examples": [], "limits": None}]},
        {"language_id": "l2", "features": []}]
    write_json(tmp_path / "features.json", feats)
    metas = [{"id": i, "name": i, "category": "c", "universe": "u", "creator": None, "year": None,
              "documentation_level": "low", "metadata_status": "unverified", "corpus": {"status": "absent"}} for i in ("l1", "l2")]
    monkeypatch.setattr("atlas.export.project_path", lambda key: tmp_path / key)
    export_all({"scripts": []}, metas, tmp_path, tmp_path)
    with (tmp_path / "language_features.csv").open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert [r["id"] for r in rows] == ["l1", "l2"]
    assert rows[0]["lexicon.ttr__value"] == "0.5" and rows[1]["lexicon.ttr__value"] == "null"
    assert rows[1]["lexicon.ttr__status"] == "unavailable"
    data = json.loads((tmp_path / "language_features.json").read_text())
    assert data[0]["features"][0]["status"] == "computed"
