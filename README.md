# Imaginary Languages Atlas

Plateforme de recherche en linguistique computationnelle : cartographie et
analyse typologique d'une trentaine de langues imaginaires, comparées aux
langues naturelles de WALS.

> La carte et les scores mesurent une **proximité typologique**. Ils
> n'indiquent ni une origine géographique, ni une parenté, ni une influence.

## État du projet

| Étape | État |
|---|---|
| 1. Audit et conception | terminée (2026-11-27) |
| 2. Constitution du corpus | en cours : catalogue de 30 langues et 6 écritures, collecte automatique opérationnelle |
| 3. Analyse linguistique | en cours : 11 langues codées (79 valeurs documentées, citations vérifiées automatiquement) |
| 4. Comparaison WALS | chargeur, correspondances (20 caractéristiques), Gower et agrégation par aire écrits et testés |
| 5. Site web | à faire |
| 6. Intégration | API en lecture seule écrite et testée |
| 7. Documentation et déploiement | documentation méthodologique commencée |

Premiers scores de proximité pour 5 langues (dothraki, espéranto, na'vi,
quenya, toki pona) : voir `docs/results.md`. Ils sont préliminaires et
reposent sur 8 à 11 caractéristiques.

## Installation

Python ≥ 3.11.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -e ".[dev,api]"
```

## Reconstruire toutes les analyses

```bash
python scripts/rebuild_all.py            # collecte, calculs, exports
python scripts/rebuild_all.py --offline  # uniquement à partir du cache local
python scripts/rebuild_all.py --force    # relance toutes les étapes
python scripts/rebuild_all.py --weights no_phonology   # test de sensibilité
```

Étapes : `collect → features → wals → harmonise → similarity → regions →
export → site_data`. Une étape dont les entrées (données, configuration, code)
n'ont pas changé est sautée ; une interruption reprend à l'étape en échec. Les
journaux sont dans `outputs/logs/`.

## Tests

```bash
python -m pytest
```

## Résultats

| Fichier | Contenu |
|---|---|
| `outputs/language_features.csv` | une ligne par langue, colonnes `<caractéristique>__value` et `__status` |
| `outputs/language_features.json` | fiche complète : valeur, statut, méthode, sources, exemples, limites |
| `outputs/pairwise_similarity.csv` | score de Gower pour chaque paire langue imaginaire / langue WALS |
| `outputs/regional_similarity.csv` | scores agrégés par aire linguistique, dispersion, robustesse |
| `outputs/wals_mapping.json` | correspondances avec WALS et leurs justifications |
| `outputs/collection_errors.csv` | sources indisponibles lors de la dernière collecte |
| `outputs/run_manifest.json` | versions et empreintes des données utilisées |

## Organisation

```
config/          configuration centrale (pipeline, catalogue, correspondances, poids, régions)
data/raw/        téléchargements bruts (non versionnés, reconstruits par le pipeline)
data/languages/  un dossier par langue : metadata.json, sources.csv, corpus, manifeste
data/scripts/    systèmes d'écriture
data/geography/  rattachement des langues WALS aux aires linguistiques
src/atlas/       paquet Python (collecte, prétraitement, linguistique, comparaison)
backend/api/     API FastAPI en lecture seule
frontend/        site (étape 5)
tests/           tests pytest et corpus fictifs de contrôle
docs/            méthodologie, sources, bibliographie, hébergement
```

## Données et licences

- Code : MIT (`LICENSE`).
- WALS (Dryer & Haspelmath 2013) et AUTOTYP : CC-BY-4.0.
- Phrases Tatoeba : CC BY 2.0 FR, identifiants d'origine conservés.
- Les corpus dont la licence n'autorise pas la redistribution restent en local
  (`corpus_local.txt`, ignoré par git) ; seules leurs références et les
  statistiques dérivées sont publiées.

Voir `docs/methodology.md`, `docs/sources.md` et `docs/bibliography.md`.
