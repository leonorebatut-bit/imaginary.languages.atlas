"""Lexique : taille du vocabulaire, diversité lexicale, fréquences.

Le TTR brut (types / tokens) diminue mécaniquement quand le corpus grandit ; il
n'est donc PAS comparable entre corpus de tailles différentes. On calcule en plus :
- MATTR (Covington & McFall 2010) : moyenne des TTR sur une fenêtre glissante ;
- MTLD (McCarthy & Jarvis 2010) : longueur moyenne des segments qui gardent un
  TTR au-dessus d'un seuil (0,72), moyenne des passes avant et arrière ;
- HD-D (McCarthy & Jarvis 2007) : espérance du nombre de types dans un
  échantillon aléatoire de 42 tokens, divisée par 42.
En dessous de `min_tokens`, ces indices valent null.
"""
from __future__ import annotations

from collections import Counter
from math import exp, lgamma

import regex

from ..schema import FeatureValue, Status, unavailable

METHOD_VERSION = "lexicon/1"


def ttr(tokens: list[str]) -> float | None:
    return len(set(tokens)) / len(tokens) if tokens else None


def mattr(tokens: list[str], window: int) -> float | None:
    n = len(tokens)
    if n < window or window <= 0:
        return None
    counts = Counter(tokens[:window])
    total = len(counts)
    for i in range(window, n):
        out_tok, in_tok = tokens[i - window], tokens[i]
        counts[out_tok] -= 1
        if counts[out_tok] == 0:
            del counts[out_tok]
        counts[in_tok] += 1
        total += len(counts)
    return total / (n - window + 1) / window


def _mtld_pass(tokens: list[str], threshold: float) -> float | None:
    factors = 0.0
    seen: set[str] = set()
    count = 0
    current_ttr = 1.0
    for tok in tokens:
        count += 1
        seen.add(tok)
        current_ttr = len(seen) / count
        if current_ttr <= threshold:
            factors += 1
            seen, count, current_ttr = set(), 0, 1.0
    if count > 0:
        factors += (1 - current_ttr) / (1 - threshold)
    return len(tokens) / factors if factors > 0 else None


def mtld(tokens: list[str], threshold: float = 0.72) -> float | None:
    if not tokens:
        return None
    fwd, bwd = _mtld_pass(tokens, threshold), _mtld_pass(tokens[::-1], threshold)
    if fwd is None or bwd is None:
        return None
    return (fwd + bwd) / 2


def _log_comb(n: int, k: int) -> float:
    return lgamma(n + 1) - lgamma(k + 1) - lgamma(n - k + 1)


def hdd(tokens: list[str], sample: int = 42) -> float | None:
    n = len(tokens)
    if n < sample:
        return None
    total = 0.0
    for freq in Counter(tokens).values():
        if n - freq < sample:
            p_absent = 0.0
        else:
            p_absent = exp(_log_comb(n - freq, sample) - _log_comb(n, sample))
        total += (1 - p_absent) / sample
    return total


def mean_word_length(tokens: list[str]) -> float | None:
    """Longueur moyenne en graphèmes (clusters Unicode), pas en octets ni en points de code."""
    if not tokens:
        return None
    return sum(len(regex.findall(r"\X", t)) for t in tokens) / len(tokens)


def top_ngrams(tokens: list[str], n: int, k: int = 20, min_count: int = 2) -> list[tuple[str, int]]:
    grams = Counter(" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1))
    return [(g, c) for g, c in grams.most_common(k) if c >= min_count]


def lexicon_features(tokens: list[str], cfg: dict) -> list[FeatureValue]:
    """Toutes les caractéristiques lexicales d'un corpus tokenisé."""
    n = len(tokens)
    m = f"{METHOD_VERSION}"
    feats: list[FeatureValue] = []
    if n == 0:
        reason = "corpus vide ou absent"
        for fid in ("token_count", "type_count", "ttr", "mattr", "mtld", "hdd", "mean_word_length", "hapax_ratio"):
            feats.append(unavailable(f"lexicon.{fid}", "lexicon", m, reason))
        return feats

    counts = Counter(tokens)
    feats.append(FeatureValue("lexicon.token_count", "lexicon", n, Status.COMPUTED, f"{m}:count", unit="tokens"))
    feats.append(FeatureValue("lexicon.type_count", "lexicon", len(counts), Status.COMPUTED, f"{m}:count", unit="formes distinctes"))
    feats.append(FeatureValue("lexicon.ttr", "lexicon", round(len(counts) / n, 6), Status.COMPUTED, f"{m}:ttr",
                              limits="dépend fortement de la taille du corpus ; ne pas comparer entre corpus"))
    feats.append(FeatureValue("lexicon.hapax_ratio", "lexicon",
                              round(sum(1 for c in counts.values() if c == 1) / len(counts), 6), Status.COMPUTED, f"{m}:hapax"))
    feats.append(FeatureValue("lexicon.mean_word_length", "lexicon", round(mean_word_length(tokens), 4), Status.COMPUTED,
                              f"{m}:graphemes", unit="graphèmes",
                              limits="dépend de l'orthographe ; ne permet pas de conclure au type morphologique"))

    small = n < cfg["min_tokens"]
    reason = f"corpus trop court ({n} tokens < {cfg['min_tokens']})"
    for fid, fn in (("mattr", lambda: mattr(tokens, cfg["mattr_window"])),
                    ("mtld", lambda: mtld(tokens, cfg["mtld_threshold"])),
                    ("hdd", lambda: hdd(tokens, cfg["hdd_sample"]))):
        val = None if small else fn()
        if val is None:
            feats.append(unavailable(f"lexicon.{fid}", "lexicon", f"{m}:{fid}", reason if small else "indice non défini sur ce corpus"))
        else:
            feats.append(FeatureValue(f"lexicon.{fid}", "lexicon", round(val, 6), Status.COMPUTED, f"{m}:{fid}"))
    return feats
