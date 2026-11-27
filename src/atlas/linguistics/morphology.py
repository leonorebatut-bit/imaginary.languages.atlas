"""Morphologie à partir d'exemples glosés (conventions de Leipzig).

Aucun analyseur morphologique automatique n'existe pour ces langues : le ratio
morphèmes/mots n'est donc calculé QUE sur des exemples segmentés et glosés
provenant d'une source identifiée (fichier glossed_examples.tsv de la langue).

Conventions de segmentation (Leipzig Glossing Rules, 2008) :
  -   frontière de morphème (affixe)
  =   frontière de clitique (compté comme morphème)
  ~   réduplication (compté comme morphème)
  <>  infixe, ex. : s<um>ulat (le contenu compte comme un morphème)
Gloses : les morphèmes grammaticaux sont en MAJUSCULES (PL, ACC, PST),
les morphèmes lexicaux en minuscules. Un morphème lexical est une racine.

Le type morphologique (agglutinant, fusionnel…) n'est jamais déduit de la
longueur des mots ni de ce ratio seul : il relève de typology.py et exige une
source documentaire.
"""
from __future__ import annotations

from dataclasses import dataclass

import regex

from ..schema import FeatureValue, Status, unavailable

METHOD_VERSION = "morphology/1"

_BOUNDARY = regex.compile(r"[-=~]")
_INFIX = regex.compile(r"<([^<>]+)>")

# Étiquettes de Leipzig (et variantes courantes) par catégorie grammaticale.
CATEGORY_LABELS: dict[str, set[str]] = {
    "gender": {"M", "F", "N", "MASC", "FEM", "NEUT", "ANIM", "INAN"},
    "number": {"SG", "PL", "DU", "PAUC", "TRI"},
    "case": {"NOM", "ACC", "GEN", "DAT", "ERG", "ABS", "LOC", "INS", "ABL", "ALL", "VOC",
             "COM", "ESS", "TRANSL", "PRTV", "OBL", "BEN"},
    "tense": {"PST", "PRS", "FUT", "PRES", "PAST", "NPST", "REM"},
}


@dataclass
class GlossedWord:
    form: str
    morphemes: list[str]
    glosses: list[str]
    infixes: int


def split_word(form: str) -> tuple[list[str], int]:
    infixes = _INFIX.findall(form)
    base = _INFIX.sub("", form)
    parts = [p for p in _BOUNDARY.split(base) if p]
    return parts + infixes, len(infixes)


def parse_example(segmented: str, gloss: str) -> list[GlossedWord]:
    """Aligne une ligne segmentée et sa glose mot à mot.

    Lève ValueError si le nombre de mots ou de morphèmes ne correspond pas :
    un exemple mal aligné ne doit pas être compté silencieusement.
    """
    words, gwords = segmented.split(), gloss.split()
    if len(words) != len(gwords):
        raise ValueError(f"{len(words)} mots mais {len(gwords)} gloses : {segmented!r}")
    out = []
    for w, g in zip(words, gwords):
        w = regex.sub(r"[.,;:!?\"«»]", "", w)
        morphs, n_inf = split_word(w)
        gl, _ = split_word(g)
        if len(morphs) != len(gl):
            raise ValueError(f"segmentation non alignée : {w!r} / {g!r}")
        out.append(GlossedWord(w, morphs, gl, n_inf))
    return out


def _is_grammatical(gloss: str) -> bool:
    # Une glose grammaticale est en capitales ; « 3SG » ou « 1PL » comptent aussi.
    letters = regex.sub(r"[^\p{L}]", "", gloss)
    return bool(letters) and letters.isupper()


def affix_positions(word: GlossedWord) -> dict[str, int]:
    """Compte préfixes, suffixes et infixes par rapport à la (première) racine."""
    linear = word.glosses[: len(word.glosses) - word.infixes]
    roots = [i for i, g in enumerate(linear) if not _is_grammatical(g)]
    if not roots:
        return {"prefix": 0, "suffix": 0, "infix": word.infixes}
    first, last = roots[0], roots[-1]
    return {"prefix": first, "suffix": len(linear) - 1 - last, "infix": word.infixes}


def categories_marked(words: list[GlossedWord]) -> dict[str, list[str]]:
    found: dict[str, set[str]] = {k: set() for k in CATEGORY_LABELS}
    for w in words:
        for g in w.glosses:
            for label in regex.split(r"[.\-]", g):
                label = regex.sub(r"^[123]", "", label)
                for cat, labels in CATEGORY_LABELS.items():
                    if label in labels:
                        found[cat].add(label)
    return {k: sorted(v) for k, v in found.items()}


def morphology_features(examples: list[dict], min_words: int = 30) -> list[FeatureValue]:
    """`examples` : dicts avec segmented, gloss, source_id, example_id."""
    m = METHOD_VERSION
    words: list[GlossedWord] = []
    sources: set[str] = set()
    errors: list[str] = []
    for ex in examples:
        try:
            words.extend(parse_example(ex["segmented"], ex["gloss"]))
            sources.add(ex["source_id"])
        except ValueError as exc:
            errors.append(f"{ex.get('example_id')}: {exc}")

    if len(words) < min_words:
        reason = (f"segmentation glosée insuffisante ({len(words)} mots < {min_words})"
                  + (f" ; {len(errors)} exemple(s) mal aligné(s)" if errors else ""))
        return [unavailable(f"morphology.{f}", "morphology", m, reason)
                for f in ("morphemes_per_word", "prefix_share", "suffix_share", "infix_count", "categories_marked")]

    srcs = sorted(sources)
    n_morph = sum(len(w.morphemes) for w in words)
    pos = {"prefix": 0, "suffix": 0, "infix": 0}
    for w in words:
        for k, v in affix_positions(w).items():
            pos[k] += v
    n_aff = sum(pos.values())
    limits_err = f"{len(errors)} exemple(s) exclu(s) pour défaut d'alignement" if errors else None
    examples_txt = [" ".join("-".join(w.morphemes) for w in words[:6])]
    feats = [
        FeatureValue("morphology.morphemes_per_word", "morphology", round(n_morph / len(words), 4), Status.COMPUTED,
                     f"{m}:leipzig_ratio", unit="morphèmes/mot", source_ids=srcs, examples=examples_txt,
                     limits=("indice de synthèse (Greenberg 1960) sur un échantillon glosé de "
                             f"{len(words)} mots ; dépend des choix de segmentation de la source")
                     + (f" ; {limits_err}" if limits_err else "")),
    ]
    if n_aff:
        feats.append(FeatureValue("morphology.prefix_share", "morphology", round(pos["prefix"] / n_aff, 4), Status.COMPUTED,
                                  f"{m}:affix_position", source_ids=srcs,
                                  limits="tous affixes confondus (flexion et dérivation), à la différence de WALS 26A"))
        feats.append(FeatureValue("morphology.suffix_share", "morphology", round(pos["suffix"] / n_aff, 4), Status.COMPUTED,
                                  f"{m}:affix_position", source_ids=srcs))
    else:
        feats.append(unavailable("morphology.prefix_share", "morphology", m, "aucun affixe dans l'échantillon"))
        feats.append(unavailable("morphology.suffix_share", "morphology", m, "aucun affixe dans l'échantillon"))
    feats.append(FeatureValue("morphology.infix_count", "morphology", pos["infix"], Status.COMPUTED, f"{m}:infix", source_ids=srcs))
    feats.append(FeatureValue("morphology.categories_marked", "morphology", categories_marked(words), Status.OBSERVED,
                              f"{m}:gloss_labels", source_ids=srcs,
                              limits="présence d'étiquettes dans les gloses ; l'absence n'est pas une preuve d'absence"))
    return feats
