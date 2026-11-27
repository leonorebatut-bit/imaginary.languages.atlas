# Hébergement

Choix validé à l'étape 1 : **site statique** sur GitHub Pages, alimenté par les
JSON précalculés (`frontend/public/data/`, copiés par l'étape `site_data` du
pipeline), et **API FastAPI en lecture seule** pour l'usage local et les tests.

| Option | Intérêt | Limites |
|---|---|---|
| GitHub Pages (retenu pour le site) | gratuit, sans mise en veille, versionné avec le code | dépôt public ; pas de calcul serveur (inutile : tout est précalculé) |
| Render / Koyeb, offre gratuite (API, optionnel) | API réelle en ligne | mise en veille après inactivité, quotas susceptibles d'évoluer |

Fonctionnement local, indépendant de tout hébergement :

```bash
pip install -e ".[api]"
uvicorn backend.api.main:app --reload     # http://127.0.0.1:8000/docs
```

Aucune clé secrète n'est nécessaire. Les variables d'environnement éventuelles
sont décrites dans `.env.example` ; le fichier `.env` est ignoré par git.

## Publication du site

Le workflow `.github/workflows/pages.yml` lance les tests Python et front à chaque
PR, puis, sur `main`, construit le site avec `BASE_PATH=/<nom du dépôt>/` et le
publie sur GitHub Pages. Il ne relance pas le pipeline : les données du site sont
versionnées dans `frontend/public/data/`. Après une modification des données,
lancer `python scripts/rebuild_all.py` et committer ce dossier.

Activation (une seule fois) : dans le dépôt GitHub, **Settings → Pages → Build
and deployment → Source : GitHub Actions**. Le site est alors servi à
`https://<compte>.github.io/imaginary.languages.atlas/`.

Le site n'utilise aucun serveur de tuiles : le fond de carte est le fichier
Natural Earth `land.geojson` (domaine public), servi avec les données.
