# Périmètre V1

## Fonctionnel
- Recherche NL sur 6–10 PDF récents (JONC/IEOM/ISEE/délibérations).
- Réponse synthétique avec 2–4 citations cliquables.
- Filtres rudimentaires par source et période (à étendre en V1.1).
- Évaluation de base (latence p95, recall@20, citations valides).

## Hors-périmètre V1
- Pas de conseils juridiques.
- Pas d’authentification fine (SSO/RBAC) en MVP.
- Pas de conteneurisation (Docker) pour la V1.

## Non-fonctionnel
- Déploiement local sans Docker.
- Temps de réponse p95 visé: ≤ 5 s CPU quantisé, ≤ 2.5 s GPU 7–8B.
- Journalisation locale des requêtes et des versions indexées.

## Normalisation des formats
- Dublin Core
- JSON‑LD