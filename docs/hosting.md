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

Le front-end (React, TypeScript, Leaflet) sera développé à l'étape 5.
