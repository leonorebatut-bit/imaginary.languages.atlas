"""Génère docs/results.md à partir des exports versionnés (résultats préliminaires).

Usage : python scripts/make_results.py   (après un `python scripts/rebuild_all.py` complet)

Sources lues : outputs/ et frontend/public/data/languages.json, tous versionnés,
donc le script fonctionne sur un dépôt fraîchement cloné. Il refuse de produire un
rapport si outputs/ et les données du site ne viennent pas des mêmes données brutes,
ou s'ils ont été produits avec un profil de poids autre que `equal`.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "frontend" / "public" / "data"
sys.path.insert(0, str(ROOT / "src"))
from atlas.config import pipeline_config  # noqa: E402

# Raison pour laquelle une langue n'a aucune (ou très peu de) caractéristique documentée.
# C'est un constat sur les sources disponibles, pas une valeur.
NO_DATA_REASONS = {
    "al_bhed": "la source (article sur le jeu) mentionne la langue sans la décrire",
    "black_speech": "seul le type agglutinant est décrit ; le reste du corpus tient en une inscription",
    "chakobsa": "la source du catalogue décrit la langue secrète circassienne du même nom, pas la langue des films Dune : à remplacer",
    "dovahzul": "la source (article sur le jeu Skyrim) ne décrit pas la langue des dragons",
    "huttese": "la source ne donne que l'origine (langues quechua) et l'usage de la langue",
    "lingua_ignota": "glossaire essentiellement lexical ; la source signale des mots fléchis à la latine (loifolum)",
    "minionese": "mélange de charabia et de mots de langues réelles, sans grammaire décrite",
    "nadsat": "argot : de l'anglais avec des emprunts au russe, selon la source",
    "newspeak": "variété de l'anglais : seuls des procédés de dérivation sont décrits",
    "trigedasleng": "la source (article sur la série) ne décrit pas la langue",
}


def read_csv(p: Path) -> list[dict]:
    with p.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def render() -> str:
    cfg = pipeline_config()
    threshold = cfg["similarity"]["min_comparable_features"]
    out = ROOT / "outputs"
    manifest = json.loads((out / "run_manifest.json").read_text(encoding="utf-8"))
    site_manifest = json.loads((SITE / "manifest.json").read_text(encoding="utf-8"))
    if site_manifest.get("raw_sha256") != manifest.get("raw_sha256"):
        raise SystemExit("outputs/ et frontend/public/data/ ne viennent pas de la même exécution : relancer rebuild_all.py")
    weights = manifest.get("weights_profile", "equal")
    if weights != "equal":
        raise SystemExit(f"outputs/ produits avec le profil de poids « {weights} » : le rapport ne décrit que le profil equal")
    site_langs = json.loads((SITE / "languages.json").read_text(encoding="utf-8"))
    profiles = {l["id"]: l["wals_profile"] for l in site_langs}
    names = {l["id"]: l["name"] for l in site_langs}
    # Valeurs documentées = lignes des fichiers documented_features.csv (ce qui a été codé).
    n_doc = {}
    for lid in names:
        f = ROOT / "data/languages" / lid / "documented_features.csv"
        n_doc[lid] = len(read_csv(f)) if f.exists() else 0
    pairs = read_csv(out / "pairwise_similarity.csv")
    regions = read_csv(out / "regional_similarity.csv")
    wals = {w["id"]: w for w in json.loads((SITE / "wals_languages.json").read_text(encoding="utf-8"))}

    order = lambda k: int(k.rstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))  # noqa: E731
    scored = sorted(l for l, p in profiles.items() if len(p) >= threshold)
    lines = [
        "# Résultats préliminaires", "",
        f"Généré par `scripts/make_results.py` à partir de `outputs/` (pipeline {manifest.get('pipeline_version')}, "
        f"WALS {cfg['reference_data']['wals']['version']}, profil de poids {weights}, seuil de {threshold} caractéristiques comparables).", "",
        "> Proximité typologique uniquement : ni origine, ni parenté, ni influence. Les valeurs documentées ont été "
        "codées par un assistant IA à partir de Wikipédia et doivent être relues.", "",
        "## Caractéristiques par langue", "",
        "| Langue | Valeurs documentées | Caractéristiques WALS | Score calculable |", "|---|---|---|---|",
    ]
    for lid in sorted(names):
        p = profiles.get(lid, {})
        ks = ", ".join(sorted(p, key=order))
        lines.append(f"| {names[lid]} | {n_doc[lid]} | {len(p)}{f' ({ks})' if ks else ''} | "
                     f"{'oui' if len(p) >= threshold else f'non (< {threshold})'} |")
    lines += ["", f"{len(scored)} langues sur {len(names)} ont un score. "
              f"{sum(1 for v in n_doc.values() if v)} ont au moins une valeur documentée.", "",
              "## Langues sans données comparables, et pourquoi", "",
              "| Langue | Raison |", "|---|---|"]
    for lid, why in sorted(NO_DATA_REASONS.items()):
        lines.append(f"| {names.get(lid, lid)} | {why} |")

    lines += ["", "## Langues WALS les plus proches", "",
              "Pour chaque langue, les 5 meilleurs scores (à score égal, la langue comparée sur le plus de "
              "caractéristiques d'abord)."]
    for lid in scored:
        ps = [p for p in pairs if p["imaginary_id"] == lid and p["score"] != "null"]
        ps.sort(key=lambda p: (-float(p["score"]), -int(p["n_compared"]), p["wals_id"]))
        lines += ["", f"### {names[lid]}", "", f"{len(ps)} langues WALS ont au moins {threshold} caractéristiques en commun.",
                  "", "| Langue WALS | Famille | Caract. comparées | Score |", "|---|---|---|---|"]
        for p in ps[:5]:
            w = wals.get(p["wals_id"], {})
            lines.append(f"| {w.get('name', p['wals_id'])} | {w.get('family') or '—'} | {p['n_compared']} | {float(p['score']):.3f} |")

    lines += ["", "## Aires linguistiques les plus proches (résultats robustes uniquement)", "",
              "Score pondéré par genre, intervalle de confiance à 95 % par bootstrap sur les genres. Une aire est "
              "robuste si au moins 10 langues et 3 genres sont comparés."]
    for lid in scored:
        rs = [r for r in regions if r["imaginary_id"] == lid and r["robust"] == "True"]
        rs.sort(key=lambda r: -float(r["score_genus_weighted"]))
        lines += ["", f"### {names[lid]}", "", "| Aire | Score | IC 95 % | Langues | Genres |", "|---|---|---|---|---|"]
        for r in rs[:5]:
            lines.append(f"| {r['area']} | {float(r['score_genus_weighted']):.3f} | "
                         f"{float(r['ci95_low']):.2f}–{float(r['ci95_high']):.2f} | {r['n_languages']} | {r['n_genera']} |")

    lines += ["", "## Lecture", "",
              "- Les rapprochements sont à lire comme un contrôle de vraisemblance du pipeline, pas comme une découverte "
              "(par exemple, l'espéranto ressemble aux langues d'Europe dont il s'inspire).",
              "- Les intervalles de confiance se chevauchent souvent entre aires : les premières places ne sont pas "
              "toujours significativement distinctes.",
              f"- Avec {threshold} à 11 caractéristiques, un seul trait modifie sensiblement le score ; un score de 1,000 "
              "peut reposer sur 8 traits concordants seulement.", ""]
    return "\n".join(lines)


def main() -> None:
    (ROOT / "docs/results.md").write_text(render(), encoding="utf-8")
    print("docs/results.md écrit")


if __name__ == "__main__":
    main()
