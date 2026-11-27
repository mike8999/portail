# Portail — mes applications

Toutes mes applications **GitHub Pages** et **Netlify** en plaques carrées, rangées par catégorie.
Adresse : https://mike8999.github.io/portail/ · page élèves : https://mike8999.github.io/portail/eleves/

## Fichiers
| Fichier | Rôle |
|---|---|
| `index.html` | la page |
| `apps.json` | la liste des applis (nom, lien, description, niveaux, mode d'emploi…) |
| `reglages.json` | réglages faits en mode édition, exportés depuis la page |
| `donnees/auto.json` | rempli automatiquement : pannes, dates de mise à jour, nouvelles applis repérées |
| `captures/` | captures d'écran (une par appli, `id.jpg`) |
| `scripts/maj.py` + `.github/workflows/maj.yml` | tâche automatique quotidienne |
| `manifest.webmanifest`, `sw.js`, `icones/` | installation et fonctionnement hors ligne |

## Fonctions
- Clic sur une plaque : ouverture dans un nouvel onglet ; au survol, capture d'écran + description
- Recherche (`/`), filtres à cocher : catégorie, niveau, hébergeur ; favoris (étoile)
- Badges **Nouveau** (30 jours), **Mis à jour** (14 jours), **Hors ligne** (l'appli ne répond plus)
- Bouton mode d'emploi si un lien est renseigné ; QR code plein écran pour projeter (`P` pour le portail)
- Mode édition (`E`) : ajouter, modifier, masquer, classer les nouveautés ; **Exporter** → remplacer `reglages.json`
- Boîte à idées vers la base Notion ; thème clair/sombre (`T`) ; installable (bouton « Installer »)

## Tâche automatique
Chaque jour vers 5 h : vérification des applis, dates, repérage des nouveaux dépôts publiés et des dossiers d'isole-x.
Captures refaites le lundi (ou quand il en manque). Lancement manuel : onglet **Actions → Mise à jour du portail → Run workflow**.
Pour repérer aussi les sites Netlify : créer un jeton (Netlify → User settings → Applications → Personal access tokens)
et l'ajouter dans **Settings → Secrets and variables → Actions** sous le nom `NETLIFY_TOKEN`.

Anciennes versions du portail conservées dans des dossiers `v1`, `v2`…
