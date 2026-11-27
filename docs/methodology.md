# Méthodologie

Ce document explique comment chaque résultat du projet est obtenu. Il est mis à
jour à chaque étape. Version du pipeline : 0.1.0.

> **Avertissement.** La carte et les scores représentent une **proximité
> typologique** entre profils de caractéristiques. Ils ne disent rien d'une
> origine géographique, d'une parenté généalogique ou d'une influence
> historique. Beaucoup de créateurs se sont inspirés de langues réelles : une
> proximité trouvée n'est pas une découverte lorsqu'elle est documentée.

## 1. Principes

1. **Aucune donnée inventée.** Une valeur inconnue vaut `null` (statut
   `unavailable`), avec la raison de son absence. Le code refuse de créer une
   valeur « documentée » sans source (`src/atlas/schema.py`).
2. **Quatre statuts distincts** pour chaque caractéristique :
   | Statut | Signification |
   |---|---|
   | `documented` | reprise d'une grammaire ou d'une description publiée, avec référence et localisation (page, section) |
   | `observed` | constatée directement dans le corpus (ex. graphèmes) |
   | `computed` | calculée par une fonction du projet (méthode versionnée) |
   | `unavailable` | non disponible : `value = null` |
3. **Données brutes séparées des données transformées** : `data/raw/` (jamais
   modifié, empreinte SHA-256 consignée), `data/processed/` (intermédiaire),
   `outputs/` (résultats).
4. **Reproductibilité** : versions figées des bases de référence, graines
   aléatoires fixées, écriture déterministe des fichiers. Deux exécutions avec
   les mêmes données et paramètres produisent des fichiers identiques octet
   pour octet (vérifié le 2026-11-27 avec `--force --offline` exécuté deux fois).

## 2. Corpus et catégories

Le catalogue (`config/catalog.yaml`) recense 30 langues ou variétés et 6
systèmes d'écriture. Les catégories sont :

| Catégorie | Définition retenue |
|---|---|
| `constructed_fictional` | langue construite pour une œuvre de fiction, avec une grammaire publiée |
| `constructed_external` | langue construite hors fiction (auxiliaire, logique, philosophique, artistique), incluse comme point de comparaison |
| `fragmentary` | langue fictive attestée seulement par un lexique ou quelques phrases |
| `idiolect` | manière de parler propre à un personnage |
| `sociolect` | variété propre à un groupe social fictif |
| `transformed_variety` | langue réelle transformée par un procédé (chiffrement, substitution lexicale, évolution fictive, appauvrissement planifié) |
| `pseudo_language` | suite sonore sans grammaire ni lexique stables |

Les **systèmes d'écriture** (Tengwar, Cirth, Aurebesh, pIqaD…) sont des objets
distincts des langues. Une relation langue-écriture n'est enregistrée que si
elle est documentée (`represents`).

Les métadonnées du catalogue (créateur, année, description) proviennent de
connaissances générales et portent le statut `metadata_status: unverified`
tant qu'elles n'ont pas été relues contre une source collectée. Le niveau de
documentation est une estimation initiale.

## 3. Collecte

`src/atlas/collection/collect.py`, étape `collect` du pipeline.

- Chaque source du catalogue est téléchargée une fois dans
  `data/raw/sources/<langue>/` avec un fichier `.meta.json` (URL, date de
  récupération, statut HTTP, SHA-256). Les téléchargements suivants lisent le
  cache.
- Politesse : délai minimal de 1,5 s entre deux requêtes vers un même serveur,
  respect de l'en-tête `Retry-After` en cas de HTTP 429.
- Une source indisponible est consignée dans `outputs/collection_errors.csv`
  et la collecte continue. Tant que ce fichier contient des erreurs, l'étape
  est relancée à chaque exécution (les sources déjà obtenues viennent du cache).
- **Corpus de phrases** : les exports Tatoeba (CC BY 2.0 FR) sont analysés. Si
  une source dépasse 5 000 phrases, un échantillon aléatoire déterministe
  (graine fixe) est conservé ; le nombre total disponible et le nombre conservé
  sont consignés dans `sources.csv` (`available_items`, `kept_items`). Chaque
  ligne du corpus est rattachée à son identifiant Tatoeba dans
  `corpus_manifest.csv`.
- **Droits d'auteur** : un corpus n'est écrit dans `corpus.txt` (versionné) que
  si la licence de sa source autorise la redistribution (CC BY, CC BY-SA, CC0,
  domaine public). Sinon il est écrit dans `corpus_local.txt`, ignoré par git ;
  seules les références et les statistiques dérivées sont publiées.
- Sans corpus, `metadata.json` indique `corpus.status = "absent"` et la
  justification.

Les articles encyclopédiques téléchargés servent de **sources documentaires**
(à lire pour coder les caractéristiques documentées). Ils ne sont pas traités
comme des corpus de la langue.

## 4. Prétraitement

`src/atlas/preprocessing/text.py`

- Normalisation Unicode NFC ; lignes vides et lignes de commentaire (`#`)
  supprimées ; espaces multiples réduits.
- Un mot est une suite de lettres et de diacritiques combinants, éventuellement
  reliée par un trait d'union ou une apostrophe interne.
- Dans les langues où l'apostrophe note un phonème (coup de glotte en klingon,
  na'vi, mando'a), elle est conservée partout dans le mot et normalisée en
  U+0027 (`orthography.apostrophe_is_letter`).
- La casse est abaissée, sauf en klingon où elle est distinctive (`q` ≠ `Q`).
- Les longueurs sont mesurées en **graphèmes** (clusters Unicode étendus).

## 5. Analyses linguistiques

Un module indépendant par domaine (`src/atlas/linguistics/`).

### 5.1 Caractéristiques documentées

Fichier `data/languages/<id>/documented_features.csv`, colonnes :

| Colonne | Contenu |
|---|---|
| `feature_id` | identifiant de la caractéristique (ex. `syntax.basic_word_order`) |
| `value` | valeur ; pour les traits comparés à WALS, libellé exact du code WALS |
| `source_id` | source citée, présente dans `sources.csv` |
| `locator` | section (ou page) de la source |
| `evidence` | citation **littérale et courte** de la source qui justifie la valeur ; plusieurs extraits sont séparés par ` [...] ` |
| `note` | précision ou limite du codage |
| `coded_by`, `coded_on` | auteur et date du codage |

**Contrôle automatique.** Au chargement, chaque citation est recherchée dans
le texte de la source téléchargée (normalisation des espaces, guillemets,
tirets et de la casse). Pour un inventaire relevé dans un tableau
(`*_inventory`), chaque symbole doit aussi figurer dans la source. Une citation
introuvable, une source inconnue ou une ligne sans citation arrêtent le
pipeline. Toute valeur documentée est donc vérifiable par un lecteur.

**Règles de codage.**
1. Une valeur n'est codée que si la source l'énonce ; aucune déduction de
   l'auteur du codage. Exemple : une source qui dit « primarily suffixing » ne
   suffit pas à coder WALS 26A (« Strongly » ou « Weakly suffixing »), qui
   exige un comptage.
2. Quand deux sources se contredisent, la caractéristique n'est pas codée et la
   contradiction est notée (ex. lojban : 18 ou 21 consonnes).
3. Une fourchette (« 22 to 24 consonants ») n'est convertie en code WALS que si
   ses deux bornes tombent dans la même classe.
4. Une valeur qui ne correspond à aucun code WALS est consignée dans
   `data/processed/harmonise_rejected.json`, jamais devinée.

État au 2026-11-27 : 11 langues codées (79 valeurs) à partir des articles de
Wikipédia en anglais (CC BY-SA 4.0) téléchargés par la collecte. Le codage a
été fait par un assistant IA (Claude) et **doit être relu** par une personne ;
les citations rendent cette relecture rapide.

### 5.2 Phonologie (`phonology.py`)

- Inventaires consonantique et vocalique : uniquement documentés (liste de
  symboles API). Leur taille est comptée ; les consonnes sont classées par mode
  d'articulation avec une table API réduite (symbole inconnu = « non_classé »).
- Structure syllabique : documentée, ou calculée à partir d'un gabarit maximal
  documenté (ex. `(C)(C)V(C)`) selon les classes de WALS 12A. Limite : WALS
  restreint aussi la nature de la seconde consonne d'attaque.
- Tons : documentés uniquement.
- Graphèmes observés : liste des graphèmes du corpus (statut `observed`).
  **Ce n'est pas un inventaire phonologique.**

### 5.3 Morphologie (`morphology.py`)

Calculée **uniquement** sur des exemples segmentés et glosés selon les règles
de Leipzig (fichier `glossed_examples.tsv`, colonnes `example_id, source_id,
locator, segmented, gloss, translation`).

- Conventions : `-` affixe, `=` clitique, `~` réduplication, `<…>` infixe ;
  gloses grammaticales en MAJUSCULES, lexicales en minuscules.
- Un exemple dont les mots ou les morphèmes ne s'alignent pas avec la glose est
  **exclu et compté**, jamais corrigé silencieusement.
- Ratio morphèmes/mots = nombre total de morphèmes / nombre de mots (indice de
  synthèse de Greenberg 1960). Calculé si au moins 30 mots glosés.
- Préfixation / suffixation : position des affixes par rapport à la racine
  (morphème glosé en minuscules). Tous affixes confondus, à la différence de
  WALS 26A qui ne considère que la flexion : cet indicateur n'est donc pas
  utilisé pour la comparaison WALS.
- Catégories marquées (genre, nombre, cas, temps) : présence d'étiquettes dans
  les gloses. L'absence d'étiquette ne prouve pas l'absence de la catégorie.

### 5.4 Syntaxe (`syntax.py`)

Ordres des constituants, adpositions, génitif, adjectif, etc. : documentés.
L'ordre objet-verbe (WALS 83A) est **déduit** de l'ordre dominant documenté
(ex. OVS → OV), avec le statut `computed`. L'ordre sujet-verbe (82A) n'est pas
déduit, car WALS le code aussi d'après les propositions intransitives.
Pour les seules variétés fondées sur l'anglais, une estimation par spaCy est
disponible (`estimate_constituent_order`, extra `[nlp]`) : elle donne la
distribution des ordres S/V/O observés dans les propositions où un sujet et un
objet ont été identifiés, avec la mention « estimation », et ne remplace
jamais une valeur documentée.

### 5.5 Lexique (`lexicon.py`)

| Indicateur | Définition |
|---|---|
| tokens, types | nombre de mots, nombre de formes distinctes |
| TTR | types / tokens ; **non comparable** entre corpus de tailles différentes |
| MATTR | moyenne des TTR sur une fenêtre glissante de 50 tokens (Covington & McFall 2010) |
| MTLD | longueur moyenne des segments dont le TTR reste au-dessus de 0,72 ; moyenne des passes avant et arrière (McCarthy & Jarvis 2010) |
| HD-D | somme, sur les types, de la probabilité d'apparaître dans un échantillon de 42 tokens tiré sans remise, divisée par 42 (loi hypergéométrique) |
| hapax | proportion de types n'apparaissant qu'une fois |
| longueur moyenne | en graphèmes |

En dessous de 100 tokens, MATTR, MTLD et HD-D valent `null`.

### 5.6 Typologie (`typology.py`)

Les étiquettes « isolante », « agglutinante », « fusionnelle »,
« polysynthétique », « analytique », « synthétique » ne sont reprises que si
une source les documente. La bande de Greenberg (analytique 1,00-1,99 ;
synthétique 2,00-2,99 ; polysynthétique ≥ 3) est fournie comme **indicateur**
calculé sur les gloses, distinct d'une classification.

### 5.7 Écriture (`writing.py`)

Type (alphabet, abjad, abugida, syllabaire, logographie), sens d'écriture et
correspondances graphèmes-phonèmes : renseignés seulement s'ils sont
documentés. Les six écritures du catalogue ont pour l'instant un type `null`.
Le lien langue-écriture (`writing.scripts`) n'a le statut `documented` que si la
fiche de l'écriture cite au moins une source ; sinon il vaut `null` (cas de
l'écriture kryptonienne, sans source au catalogue).

## 6. Comparaison avec WALS

### 6.1 Données

WALS Online, jeu de données CLDF v2020.4 (CC-BY-4.0), lu directement avec
pandas (`wals_loader.py`). Les lignes de regroupement de `languages.csv`
(`family-…`, `genus-…`) sont écartées : 2 662 langues sont retenues.

### 6.2 Correspondances

`config/feature_mapping.yaml`, exporté dans `outputs/wals_mapping.json`.
20 caractéristiques du projet sont associées à un chapitre WALS dont elles
reprennent la définition (liste et justifications dans le fichier). Les
libellés sont revérifiés contre `codes.csv` au chargement : une divergence
arrête le pipeline. Les valeurs numériques (tailles d'inventaires) sont
converties selon les seuils des chapitres 1 et 2.

Caractéristiques **exclues** du calcul faute d'équivalent WALS : indices de
diversité lexicale, longueur des mots, ratio morphèmes/mots, parts de
préfixes et suffixes tous affixes confondus, graphèmes observés.

### 6.3 Similarité de Gower

$$S(a,b) = \frac{\sum_k w_k\,\delta_k\,s_k}{\sum_k w_k\,\delta_k}$$

- $\delta_k = 1$ si la caractéristique $k$ est renseignée pour les deux langues
  et $w_k > 0$, sinon 0 : **les données manquantes sont exclues du
  dénominateur** ;
- variable nominale : $s_k = 1$ si les valeurs sont identiques, 0 sinon ;
- variable ordinale à $K$ niveaux : $s_k = 1 - |r_a - r_b| / (K-1)$ ; un code
  hors échelle (49A « Exclusively borderline case-marking ») est traité comme
  nominal ;
- $S \in [0, 1]$ ;
- si moins de **8** caractéristiques sont comparables, aucun score n'est
  attribué (`null`).

Pour chaque paire : nombre de caractéristiques comparées, identiques,
différentes, score, listes des caractéristiques concordantes et divergentes
(`outputs/pairwise_similarity.csv`).

Poids : `config/weights.yaml`. Profil par défaut `equal` (tous à 1). Les profils
`word_order_heavy` et `no_phonology` servent aux tests de sensibilité :
`python scripts/rebuild_all.py --weights no_phonology`.

## 7. Agrégation géographique

### 7.1 Définition des régions

Choix validé : chaque langue WALS est placée à ses coordonnées WALS (zone
principale), et les régions suivent des **aires linguistiques** plutôt que des
frontières politiques. On utilise la variable `Area` du registre AUTOTYP
(Bickel, Nichols et al. ; CC-BY-4.0), soit 24 aires.

Rattachement d'une langue WALS (`data/geography/wals_language_areas.csv`) :

| Méthode | Langues (WALS v2020.4) |
|---|---|
| Glottocode présent dans AUTOTYP | 2 496 |
| Langue AUTOTYP la plus proche à moins de 500 km | 165 |
| Non rattachée (exclue) | 1 (International Sign) |

### 7.2 Calcul

Pour une langue imaginaire et une aire, parmi les langues WALS qui ont un score :

- **score régional** = moyenne des moyennes par genre WALS, pour qu'un genre
  très représenté ne domine pas l'aire ; moyenne simple et médiane fournies ;
- **dispersion** : écart-type, écart interquartile, intervalle de confiance à
  95 % par bootstrap sur les genres (1 000 tirages, graine fixe) ;
- **robustesse** : une aire est `robust` si elle compte au moins 10 langues et
  3 genres comparés. Les autres résultats sont affichés comme peu robustes.

## 8. Limites connues

- Les corpus disponibles à ce jour (Tatoeba) sont des phrases d'apprenants et de
  contributeurs : elles reflètent l'usage communautaire, pas nécessairement les
  textes canoniques des créateurs. Certaines phrases peuvent reprendre des
  œuvres protégées ; à surveiller lors de la relecture.
- Les tailles de corpus vont de quelques centaines à plusieurs milliers de
  phrases ; seuls MATTR, MTLD et HD-D sont comparables entre corpus.
- Les caractéristiques documentées viennent pour l'instant d'articles
  encyclopédiques. Elles devront être confrontées aux grammaires de référence
  (Okrand pour le klingon, Peterson pour le dothraki, etc.) lorsque celles-ci
  seront accessibles.
- Seules 5 langues sur 11 atteignent le seuil de 8 caractéristiques
  comparables (voir `docs/results.md`). Les scores reposent sur 8 à 11
  caractéristiques : ils restent indicatifs.
- Biais d'échantillon WALS : les langues comparées sont celles qui ont au moins
  8 des 20 caractéristiques codées, surtout celles de l'échantillon de 200
  langues de WALS.
- Les données WALS sont lacunaires : la plupart des langues n'ont qu'une partie
  des 20 caractéristiques utilisées, d'où le seuil de 8.
