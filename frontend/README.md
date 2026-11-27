# Site web (étape 5)

React 18 + TypeScript + Vite + Leaflet. Le site est entièrement statique : il lit
les JSON de `public/data/`, produits par l'étape `site_data` de
`python scripts/rebuild_all.py`. Il ne calcule aucun score ; il filtre et affiche.
Ne pas modifier `public/data/` à la main.

```bash
cd frontend
npm ci
npm run dev        # http://localhost:5173
npm test           # tests vitest (filtres, couleurs, pages)
npm run build      # vérification TypeScript puis construction dans dist/
BASE_PATH=/imaginary.languages.atlas/ npm run build   # chemins pour GitHub Pages
```

| Page | Adresse | Contenu |
|---|---|---|
| Accueil | `#/` | projet, objectifs, méthodes, corpus, bases utilisées, limites |
| Carte | `#/carte?langue=<id>` | langues WALS colorées selon le score de leur aire, filtres combinables, détail d'une aire |
| Langues | `#/langues` | recherche, tri par colonne, filtres |
| Fiche | `#/langues/<id>` | 10 sections : présentation, corpus et sources, phonologie, morphologie, syntaxe, typologie, lexique, écriture, comparaison WALS, références |
| Comparaison | `#/comparaison?langue=<id>&wals=<code>` | langues WALS les plus proches, puis tableau caractéristique par caractéristique |

Le routage par `#` évite toute configuration serveur sur GitHub Pages.
