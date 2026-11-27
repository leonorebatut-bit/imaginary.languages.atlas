"""Assemblage des caractéristiques d'une langue à partir de ses fichiers."""
from __future__ import annotations

import csv
from pathlib import Path

from .linguistics.documented import load_documented
from .linguistics.lexicon import lexicon_features
from .linguistics.morphology import morphology_features
from .linguistics.phonology import phonology_features
from .linguistics.syntax import syntax_features
from .linguistics.typology import typology_features
from .linguistics.writing import writing_features
from .preprocessing.text import clean_corpus, graphemes, tokenize
from .schema import FeatureValue

GLOSS_COLUMNS = ["example_id", "source_id", "locator", "segmented", "gloss", "translation"]


def read_corpus(ldir: Path) -> str:
    for name in ("corpus.txt", "corpus_local.txt"):
        p = ldir / name
        if p.exists():
            return p.read_text(encoding="utf-8")
    return ""


def read_glossed(ldir: Path) -> list[dict]:
    p = ldir / "glossed_examples.tsv"
    if not p.exists():
        return []
    with p.open(encoding="utf-8", newline="") as fh:
        return [r for r in csv.DictReader(fh, delimiter="\t") if (r.get("segmented") or "").strip()]


def language_features(lang: dict, ldir: Path, source_ids: set[str], scripts: dict[str, dict], cfg: dict,
                      source_texts: dict[str, str] | None = None) -> list[FeatureValue]:
    ortho = lang.get("orthography") or {}
    text = clean_corpus(read_corpus(ldir))
    tokens = tokenize(text, apostrophe_is_letter=ortho.get("apostrophe_is_letter", False),
                      case_sensitive=ortho.get("case_sensitive", False))
    documented = load_documented(ldir / "documented_features.csv", source_ids, source_texts)
    glossed = [g for g in read_glossed(ldir) if g.get("source_id") in source_ids]

    feats: list[FeatureValue] = []
    feats += phonology_features(documented, graphemes(tokens))
    morph = morphology_features(glossed)
    feats += morph
    # Caractéristiques morphologiques documentées (genre, cas, type…) reprises telles quelles.
    feats += [f for k, f in sorted(documented.items()) if k.startswith("morphology.")]
    feats += syntax_features(documented)
    feats += typology_features(documented, {f.feature_id: f for f in morph})
    feats += lexicon_features(tokens, cfg["lexicon"])
    feats += writing_features(lang, scripts)

    # Dédoublonnage : la première occurrence d'un identifiant l'emporte.
    seen, out = set(), []
    for f in feats:
        if f.feature_id not in seen:
            seen.add(f.feature_id)
            out.append(f)
    return out
