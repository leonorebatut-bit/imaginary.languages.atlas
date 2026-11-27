"""Nettoyage et tokenisation des corpus.

Conventions (docs/methodology.md §4) :
- normalisation Unicode NFC, espaces normalisés, lignes vides et commentaires
  (lignes commençant par `#`) retirés ;
- un mot = suite de lettres (\\p{L}) et de diacritiques combinants (\\p{M}),
  éventuellement reliée par des traits d'union ou des apostrophes internes ;
- l'apostrophe est une lettre à part entière dans certaines langues (coup de
  glotte en klingon, en na'vi) : `apostrophe_is_letter=True` la conserve aussi
  en début et fin de mot ;
- la casse est abaissée pour le lexique (`casefold`), sauf en klingon où la
  casse est distinctive (q / Q) : `case_sensitive=True`.
"""
from __future__ import annotations

import unicodedata

import regex

APOSTROPHES = "'’ʼ"   # ' ’ ʼ
_LETTER = r"[\p{L}\p{M}]"
_APO = f"[{APOSTROPHES}]"
_WORD_INTERNAL = regex.compile(rf"{_LETTER}+(?:(?:{_APO}|-){_LETTER}+)*")
_WORD_APO = regex.compile(rf"(?:{_APO}|{_LETTER})+(?:-(?:{_APO}|{_LETTER})+)*")
_SENT_SPLIT = regex.compile(r"(?<=[.!?…])\s+")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace(" ", " ").replace("\t", " ")
    return text


def clean_corpus(raw: str) -> str:
    lines = []
    for line in normalize(raw).splitlines():
        line = regex.sub(r" {2,}", " ", line).strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return "\n".join(lines)


def tokenize(text: str, apostrophe_is_letter: bool = False, case_sensitive: bool = False) -> list[str]:
    pattern = _WORD_APO if apostrophe_is_letter else _WORD_INTERNAL
    tokens = pattern.findall(normalize(text))
    if apostrophe_is_letter:
        # Normalise les variantes typographiques d'apostrophe vers U+0027.
        tokens = [regex.sub(_APO, "'", t) for t in tokens]
    return tokens if case_sensitive else [t.casefold() for t in tokens]


def sentences(text: str) -> list[str]:
    out: list[str] = []
    for line in clean_corpus(text).splitlines():
        out.extend(s.strip() for s in _SENT_SPLIT.split(line) if s.strip())
    return out


def graphemes(tokens: list[str]) -> list[str]:
    """Graphèmes (clusters étendus Unicode) observés dans une liste de tokens.

    Attention : un graphème observé n'est pas un phonème (voir phonology.py).
    """
    return [g for t in tokens for g in regex.findall(r"\X", t) if g != "-"]
