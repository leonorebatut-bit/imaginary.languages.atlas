"""Syntaxe.

Aucun analyseur syntaxique n'existe pour les langues construites : les ordres
de constituants viennent des grammaires (statut `documented`). Pour les seules
variétés fondées sur l'anglais (Yoda, novlangue, Nadsat, Trigedasleng…),
`estimate_constituent_order` peut utiliser spaCy (extra optionnel [nlp]).
Le résultat est une ESTIMATION : distribution des ordres observés dans les
phrases où un sujet et un objet direct ont été identifiés, jamais présentée
comme l'ordre dominant certain.
"""
from __future__ import annotations

from collections import Counter

from ..schema import FeatureValue, Status, unavailable

METHOD_VERSION = "syntax/1"

SYNTAX_FEATURES = (
    "basic_word_order", "subject_verb_order", "object_verb_order", "adposition_order",
    "genitive_noun_order", "adjective_noun_order", "demonstrative_noun_order",
    "numeral_noun_order", "relative_clause_noun_order", "polar_question_strategy",
    "negative_morpheme_type", "subordination",
)


def order_from_positions(s: int, v: int, o: int) -> str:
    return "".join(k for _, k in sorted([(s, "S"), (v, "V"), (o, "O")]))


def estimate_constituent_order(sentences: list[str], model: str = "en_core_web_sm", min_clauses: int = 20) -> FeatureValue:
    m = f"{METHOD_VERSION}:spacy:{model}"
    try:
        import spacy  # import paresseux : dépendance optionnelle
        nlp = spacy.load(model)
    except Exception as exc:  # noqa: BLE001 - absence du modèle = indisponible
        return unavailable("syntax.estimated_constituent_order", "syntax", m, f"spaCy indisponible : {exc}")
    orders: Counter[str] = Counter()
    examples: list[str] = []
    for doc in nlp.pipe(sentences):
        for tok in doc:
            if tok.pos_ not in ("VERB", "AUX"):
                continue
            subj = [c for c in tok.children if c.dep_ in ("nsubj", "nsubjpass")]
            obj = [c for c in tok.children if c.dep_ in ("dobj", "obj")]
            if subj and obj:
                order = order_from_positions(subj[0].i, tok.i, obj[0].i)
                orders[order] += 1
                if len(examples) < 5:
                    examples.append(f"{doc.text} [{order}]")
    total = sum(orders.values())
    if total < min_clauses:
        return unavailable("syntax.estimated_constituent_order", "syntax", m,
                           f"trop peu de propositions S-V-O identifiées ({total} < {min_clauses})")
    dist = {k: round(v / total, 4) for k, v in sorted(orders.items())}
    return FeatureValue("syntax.estimated_constituent_order", "syntax", dist, Status.COMPUTED, m, unit="proportion",
                        examples=examples,
                        limits=("estimation par un modèle entraîné sur l'anglais standard ; les ordres non canoniques "
                                "peuvent être mal analysés. Ne remplace pas une valeur documentée."))


def syntax_features(documented: dict[str, FeatureValue]) -> list[FeatureValue]:
    out = []
    for f in SYNTAX_FEATURES:
        fid = f"syntax.{f}"
        out.append(documented.get(fid) or unavailable(fid, "syntax", METHOD_VERSION, "non documenté"))
    return out
