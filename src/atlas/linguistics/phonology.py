"""Phonologie.

Principe : un inventaire phonologique vient d'une description documentée
(statut `documented`), jamais de l'orthographe seule. Le corpus ne fournit que
des graphèmes observés (statut `observed`), utiles pour contrôler la
cohérence entre l'orthographe et l'inventaire décrit.
"""
from __future__ import annotations

from collections import Counter

import regex

from ..schema import FeatureValue, Status, unavailable

METHOD_VERSION = "phonology/1"

# Table réduite des symboles API consonantiques par mode d'articulation.
# Un symbole absent de la table est signalé, pas deviné.
MANNER = {
    "plosive": set("pbtdʈɖcɟkɡgqɢʔ"),
    "nasal": set("mɱnɳɲŋɴ"),
    "trill": set("ʙrʀ"),
    "tap_flap": set("ⱱɾɽ"),
    "fricative": set("ɸβfvθðszʃʒʂʐçʝxɣχʁħʕhɦ"),
    "lateral_fricative": set("ɬɮ"),
    "approximant": set("ʋɹɻjɰw"),
    "lateral_approximant": set("lɭʎʟ"),
}
_DIACRITICS = regex.compile(r"[\p{M}ːˑʰʷʲˠˤⁿˡ]")


def split_inventory(value: str) -> list[str]:
    return [s for s in value.split() if s]


def consonant_manner(symbol: str) -> str | None:
    base = _DIACRITICS.sub("", symbol)
    if regex.match(r"^(ts|dz|tʃ|dʒ|tɕ|dʑ|pf|tɬ|kx)", base):
        return "affricate"
    for manner, chars in MANNER.items():
        if base[:1] in chars:
            return manner
    return None


def classify_syllable_template(template: str) -> str | None:
    """Classe un gabarit syllabique maximal documenté (ex. « (C)(C)V(C) ») selon WALS 12A.

    Simple : (C)V ; Moderately complex : coda simple et attaque d'au plus deux
    consonnes ; Complex : au-delà. Limite : WALS restreint aussi la nature de la
    seconde consonne d'attaque, ce que le gabarit seul ne dit pas.
    """
    t = template.replace("(", "").replace(")", "").upper()
    if t.count("V") != 1 or regex.search(r"[^CV]", t):
        return None
    onset, coda = t.split("V")
    if len(onset) <= 1 and len(coda) == 0:
        return "Simple"
    if len(onset) <= 2 and len(coda) <= 1:
        return "Moderately complex"
    return "Complex"


def phonology_features(documented: dict[str, FeatureValue], graphemes: list[str]) -> list[FeatureValue]:
    m = METHOD_VERSION
    feats: list[FeatureValue] = []

    def doc(fid: str) -> FeatureValue | None:
        return documented.get(f"phonology.{fid}")

    for kind in ("consonant", "vowel_quality"):
        inv = doc(f"{kind}_inventory")
        fid = f"phonology.{kind}_inventory_size"
        if doc(f"{kind}_inventory_size"):
            feats.append(doc(f"{kind}_inventory_size"))
        elif inv:
            symbols = split_inventory(inv.value)
            feats.append(FeatureValue(fid, "phonology", len(symbols), Status.COMPUTED, f"{m}:count_documented_inventory",
                                      unit="phonèmes", source_ids=inv.source_ids, examples=[" ".join(symbols)]))
        else:
            feats.append(unavailable(fid, "phonology", m, "aucun inventaire documenté", unit="phonèmes"))
        if inv:
            feats.append(inv)

    cons = doc("consonant_inventory")
    if cons:
        manners = Counter(consonant_manner(s) or "non_classé" for s in split_inventory(cons.value))
        feats.append(FeatureValue("phonology.consonant_types", "phonology", dict(sorted(manners.items())), Status.COMPUTED,
                                  f"{m}:ipa_manner_table", source_ids=cons.source_ids,
                                  limits="table API réduite ; les symboles non reconnus sont comptés « non_classé »"))
    else:
        feats.append(unavailable("phonology.consonant_types", "phonology", m, "aucun inventaire documenté"))

    syl = doc("syllable_structure")
    tmpl = doc("syllable_template")
    if syl:
        feats.append(syl)
    elif tmpl and classify_syllable_template(tmpl.value):
        feats.append(FeatureValue("phonology.syllable_structure", "phonology", classify_syllable_template(tmpl.value),
                                  Status.COMPUTED, f"{m}:template_to_wals12A", source_ids=tmpl.source_ids,
                                  examples=[tmpl.value], limits=classify_syllable_template.__doc__.split("Limite : ")[1].strip()))
    else:
        feats.append(unavailable("phonology.syllable_structure", "phonology", m, "structure syllabique non documentée"))

    tone = doc("tone")
    feats.append(tone or unavailable("phonology.tone", "phonology", m, "présence de tons non documentée"))

    if graphemes:
        counts = Counter(graphemes)
        feats.append(FeatureValue("phonology.observed_graphemes", "phonology", sorted(counts), Status.OBSERVED,
                                  f"{m}:corpus_graphemes", unit="graphèmes",
                                  limits="graphèmes de l'orthographe du corpus : ce n'est PAS un inventaire phonologique"))
    else:
        feats.append(unavailable("phonology.observed_graphemes", "phonology", m, "corpus absent"))
    return feats
