# Guide d'utilisation

Ce guide explique comment reproduire les analyses, lire les résultats, ajouter
une langue, coder une caractéristique et relire le codage. Les choix
scientifiques sont justifiés dans `docs/methodology.md`.

## 1. Installer

Python ≥ 3.11 et, pour le site, Node.js ≥ 20.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -e ".[dev,api]"
cd frontend && npm ci && cd ..
```

Aucune clé secrète n'est nécessaire. Les variables d'environnement facultatives
sont décrites dans `.env.example` (par exemple `ATLAS_USER_AGENT`).

## 2. Reproduire les analyses

```bash
python scripts/rebuild_all.py              # collecte + tous les calculs
python scripts/rebuild_all.py --offline    # sans réseau, depuis data/raw/
python scripts/rebuild_all.py --force      # relance toutes les étapes
python scripts/make_results.py             # régénère docs/results.md
python -m pytest                           # tests Python (dont l'intégration)
cd frontend && npm test                    # tests du site
```

Une étape dont les entrées n'ont pas changé est sautée. Après une interruption,
une nouvelle commande reprend à l'étape en échec. Les journaux sont dans
`outputs/logs/`.

La collecte respecte les serveurs : une requête toutes les 1,5 s par site, avec
une attente après une réponse « trop de requêtes » (HTTP 429). Une source
indisponible est notée dans `outputs/collection_errors.csv`, et la collecte est
retentée au lancement suivant.

## 3. Lire les résultats

| Où | Quoi |
|---|---|
| Site (`cd frontend && npm run dev`) | carte, liste, fiches, comparaison |
| API (`uvicorn backend.api.main:app`) | `/api/languages`, `/api/languages/{id}`, `/{id}/regions`, `/{id}/nearest`, `/api/wals/mapping` ; documentation sur `/docs` |
| `outputs/*.csv` et `*.json` | exports complets, décrits dans le README |
| `docs/results.md` | synthèse des résultats préliminaires |

Un score mesure une proximité typologique, pas une origine, une parenté ou une
influence. Une langue sans score n'a pas assez de caractéristiques comparables
(8 au minimum) : ce n'est pas une proximité nulle.

## 4. Ajouter une langue

1. Ajouter une entrée dans `config/catalog.yaml`, sur le modèle des autres :
   `id`, `name`, `category`, `universe`, `creator`, `year`, `description`,
   `documentation_level`, `corpus_type`, `scripts`, `metadata_status: unverified`
   et `sources`. Une valeur inconnue vaut `null`.
2. Dans `sources`, citer des sources accessibles et indiquer leur licence. Un
   corpus de phrases (`type: sentence_corpus`) n'est redistribué que si sa
   licence le permet ; sinon, il reste en local dans `corpus_local.txt`.
3. **Ajouter une source uniquement en fin de liste.** Les identifiants
   (`<id>-s01`, `-s02`…) dépendent de la position : insérer une source au
   milieu changerait les références des valeurs déjà codées.
4. Lancer `python scripts/rebuild_all.py`. Le dossier `data/languages/<id>/`
   est créé, avec `metadata.json`, `sources.csv` et le corpus éventuel.

## 5. Coder une caractéristique documentée

Les valeurs vont dans `data/languages/<id>/documented_features.csv` :

```
feature_id,value,source_id,locator,evidence,note,coded_by,coded_on
syntax.basic_word_order,SOV,atlantean-s01,§ Grammar,"Atlantean has a strict subject–object–verb word order",,"Prénom Nom",2026-11-27
```

Règles, vérifiées automatiquement quand c'est possible :

- **`evidence`** est une citation littérale de la source, qui doit justifier la
  valeur elle-même, et pas seulement la section. Plusieurs extraits se séparent
  par ` [...] `. Le pipeline cherche chaque extrait dans le texte téléchargé et
  échoue s'il ne le trouve pas, ou si la source n'a pas été téléchargée.
- Pour un **inventaire** (`phonology.consonant_inventory`,
  `phonology.vowel_quality_inventory`), citer les lignes du tableau de la source,
  par exemple `Nasal | m | n | | ŋ`. Chaque symbole est recherché dans la source.
  Ne jamais déduire un inventaire de l'orthographe.
- **`value`** reprend l'intitulé exact de WALS pour les caractéristiques mises en
  correspondance (voir `config/feature_mapping.yaml`) : `SOV`, `Noun-Adjective`,
  `Plural suffix`, `6-7 cases`… Une valeur inconnue de WALS est écartée et notée
  dans `data/processed/harmonise_rejected.json`.
- Ne jamais coder un type morphologique (agglutinant, fusionnel…) à partir de la
  seule longueur des mots : il faut qu'une source le dise.
- Si deux sources se contredisent, ne pas coder, et noter la contradiction dans
  `docs/methodology.md`.
- Pour une langue à plusieurs versions, coder une seule version, et l'indiquer
  dans `note`.
- `note` sert aussi à signaler une limite : valeur dominante mais non exclusive,
  exemples peu nombreux, etc.

## 6. Relire le codage

Les valeurs actuelles ont été codées par un assistant IA (`coded_by` vaut
« Claude (assistant IA), à relire »). Pour chacune :

1. Ouvrir la source (`sources.csv`, colonne `url`) à l'endroit indiqué par `locator`.
2. Vérifier que la citation dit bien ce que la valeur affirme, et que la valeur
   correspond à la définition WALS de la caractéristique.
3. Si c'est juste, remplacer `coded_by` par votre nom et mettre `coded_on` à la
   date de la relecture. Sinon, corriger ou supprimer la ligne.
4. Quand toutes les métadonnées d'une langue sont vérifiées dans une source,
   passer `metadata_status` à `verified` dans `config/catalog.yaml`. Le site
   cesse alors d'afficher l'avertissement « métadonnées non encore relues ».
5. Relancer `python scripts/rebuild_all.py`, `python scripts/make_results.py`
   et `python -m pytest`, puis committer.

## 7. Publier le site

Le workflow `.github/workflows/pages.yml` publie le site à chaque fusion sur
`main`. Les données du site (`frontend/public/data/`) sont versionnées : après
un changement de données, committer ce dossier avec les exports. Voir
`docs/hosting.md` pour l'activation de GitHub Pages.
