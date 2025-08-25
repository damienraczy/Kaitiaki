# Kaitiaki — Documentation

Cette documentation couvre la conception, l’installation, le développement, les tests, l’exploitation et la conformité du projet **Kaitiaki**.

## Plan
- 00-produit/
  - overview.md : présentation du produit
  - scope.md : périmètre fonctionnel et non-fonctionnel
  - disclaimer.md : avertissements et limites d’usage
- 01-architecture/
  - architecture.md : vue d’ensemble technique
  - rag-pipeline.md : pipeline RAG hybride détaillé
  - data-model.md : schémas de données et formats d’échange
  - security.md : sécurité, souveraineté, RBAC
  - operations.md : vues déploiement et exécution
- 02-installation/
  - prerequisites.md : prérequis matériels et logiciels
  - quickstart.md : installation accélérée
  - configuration.md : paramètres applicatifs
  - run-local.md : lancement local sans Docker
- 03-developpement/
  - repo-structure.md : arborescence du repo
  - coding-standards.md : conventions de code
  - contributing.md : workflow Git, PR, releases
  - api-spec.md : contrat d’API FastAPI
  - data-ingestion.md : ingestion, parsing, normalisation, indexation
  - tuning-retrieval.md : réglages dense/BM25/rerank
- 04-tests/
  - test-plan.md : stratégie de test
  - evaluation-metrics.md : métriques (p95, recall@20, citations valides)
  - manual-checklist.md : recette fonctionnelle
- 05-operations/
  - monitoring.md : observabilité
  - backup-restore.md : sauvegarde et restauration
  - troubleshooting.md : résolution d’incidents
- 06-legal/
  - licenses.md : licences logicielles
- 07-roadmap/
  - roadmap.md : phases du produit
  - changelog.md : journal des changements
- 08-branding/
  - naming.md : nommage et positionnement
  - ui-copy.md : ton et messages UI

Pour démarrer, lisez **02-installation/quickstart.md**, puis **03-developpement/api-spec.md** et **01-architecture/rag-pipeline.md**.
