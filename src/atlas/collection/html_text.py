"""Conversion d'une page HTML (Wikipédia) en texte brut découpé par sections.

Sert à deux choses : lire les sources pour coder les caractéristiques
documentées, et vérifier automatiquement que chaque citation de preuve
(`evidence`) figure bien dans la source.
"""
from __future__ import annotations

import unicodedata
from pathlib import Path

import regex
from bs4 import BeautifulSoup

_DROP = ["script", "style", "sup", "table.navbox", "div.navbox", "div.reflist", "ol.references",
         "span.mw-editsection", "div.mw-references-wrap", "style"]


def normalize_for_match(text: str) -> str:
    """Normalisation tolérante : NFC, espaces fusionnés, guillemets et tirets unifiés, casse ignorée."""
    t = unicodedata.normalize("NFC", text)
    t = t.translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-",
                                   "—": "-", " ": " ", " ": " ", " ": " "}))
    return regex.sub(r"\s+", " ", t).strip().casefold()


def html_sections(html: str) -> list[tuple[str, str]]:
    """Renvoie [(titre de section, texte)] dans l'ordre du document. Les tableaux sont conservés."""
    soup = BeautifulSoup(html, "html.parser")
    # Une page peut contenir plusieurs blocs mw-parser-output (bandeaux, indicateurs) : on prend le plus long.
    blocks = soup.select("#mw-content-text div.mw-parser-output") or soup.select("div.mw-parser-output")
    content = max(blocks, key=lambda b: len(b.get_text())) if blocks else (soup.body or soup)
    for sel in _DROP:
        for el in content.select(sel):
            el.decompose()
    sections: list[tuple[str, list[str]]] = [("(introduction)", [])]
    for el in content.find_all(["h2", "h3", "h4", "p", "li", "table", "dd", "dl"], recursive=True):
        if el.name in ("h2", "h3", "h4"):
            sections.append((el.get_text(" ", strip=True), []))
        elif el.name == "table":
            rows = [" | ".join(c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])) for tr in el.find_all("tr")]
            sections[-1][1].append("\n".join(r for r in rows if r))
        elif el.find_parent("table") is None and el.find_parent(["li", "dd"]) is None:
            sections[-1][1].append(el.get_text(" ", strip=True))
    return [(t, "\n".join(x for x in parts if x)) for t, parts in sections]


def source_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    if "<html" in raw[:2000].lower():
        return "\n\n".join(f"## {t}\n{x}" for t, x in html_sections(raw))
    return raw
