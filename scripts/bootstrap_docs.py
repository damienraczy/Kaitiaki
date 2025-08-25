#!/usr/bin/env python3
# scripts/bootstrap_docs.py
from __future__ import annotations
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "documentation"

FILES: dict[str, str] = {
    # ========== documentation/ ==========
    "documentation/README.md": """# Kaitiaki — Documentation

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
""",

    # ========== 00-produit ==========
    "documentation/00-produit/overview.md": """# Présentation produit

**Kaitiaki** est un assistant de veille stratégique pour la Nouvelle-Calédonie. Il interroge et synthétise des publications publiques (JONC, ISEE, IEOM, délibérations) et fournit des réponses sourcées.

## Objectifs
- Recherche en langage naturel avec réponses concises et citations exactes.
- Synthèse thématique par secteurs (BTP, énergie, emploi).
- Filtrage temporel simple (mois/trimestre/année).
- Évolutivité vers opendata et indicateurs.

## Publics
- Entreprises industrielles, consultants, fédérations professionnelles.
- Journalistes, institutions, directions support.

## Différenciants
- Souveraineté et on-prem par conception.
- Hybridation dense + BM25 + reranking cross-encoder.
- Citations robustes (doc/page/snippet), traçabilité des versions.
""",

    "documentation/00-produit/scope.md": """# Périmètre V1

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
""",

    "documentation/00-produit/disclaimer.md": """# Avertissements

- Kaitiaki fournit des **synthèses d’informations publiques**. Il ne s’agit **pas** d’un avis juridique ou d’un conseil professionnel.
- Les réponses doivent être **vérifiées** via les citations et documents sources.
- En cas d’ambiguïté, la source officielle prévaut.
""",

    # ========== 01-architecture ==========
    "documentation/01-architecture/architecture.md": """# Architecture technique

## Vue d’ensemble
- Front minimal : FastAPI + templates HTML.
- Backend : Python 3.11, FastAPI.
- Orchestration RAG : Haystack 2.x.
- Stockage :
  - Qdrant pour embeddings denses.
  - BM25 local (rank-bm25, pickle) en MVP.
- Modèles :
  - Embeddings : all-MiniLM-L6-v2 (ou équivalent FR/EN).
  - Reranker : BAAI/bge-reranker-base.
  - LLM : Llama 3.1-8B ou Mistral 7B via API locale OpenAI-like.

## Flux
1. Ingestion PDF → extraction texte → normalisation → chunking.
2. Indexation :
   - Écriture des chunks dans Qdrant + embeddings.
   - Construction d’un index BM25 local.
3. Requête :
   - Dense top-K + BM25 top-K → fusion RRF → reranking cross-encoder → génération LLM.
4. Restitution : réponse + citations (doc/page/snippet).

## Évolutions
- Ajout OpenSearch pour BM25 avancé, filtres par champs et agrégations.
- Ajout opendata pour indicateurs (tableaux/graphes).
- Couches KG/ontologie ciblées (post-V1).
""",

    "documentation/01-architecture/rag-pipeline.md": """# Pipeline RAG hybride

## Étapes
1. Prétraitement : extraction, nettoyage, segmentation (1 200–1 600 caractères, overlap 200–300).
2. Retrieval :
   - Dense (embeddings) top_k_dense par similarité cosinus.
   - BM25 top_k_bm25 via index local.
3. Fusion : Reciprocal Rank Fusion (param k=60 par défaut).
4. Reranking : cross-encoder sur top-K fusionné (25 par défaut).
5. Génération : prompt “quote-first”, température 0.2, max_tokens 600.

## Paramètres par défaut
- top_k_dense: 20
- top_k_bm25: 20
- rerank_top_k: 25
- fusion: RRF (k=60)

## Citations
- doc_id, page, extrait (≥ 60 caractères).
- Conformes au contenu réellement passé au LLM.
""",

    "documentation/01-architecture/data-model.md": """# Modèle de données

## Fichiers intermédiaires
- `*.pages.json` :
  - doc_id, pages[{page:int, text:str}]
- `*.normalized.json` :
  - doc_id, date, chunks[{doc_id, date, page, text, source}]

## Indices
- Qdrant : documents = chunks, metadata = {doc_id, page, date, source}, embedding 384-d.
- BM25 local : tokenisation simple FR/EN, fichiers `bm25_index.pkl`, `bm25_meta.json`.

## API
- POST /query : {text, sources?, date_from?, date_to?, top_k?}
- Réponse : {answer, citations[], latency_ms}
""",

    "documentation/01-architecture/security.md": """# Sécurité et souveraineté

- Données locales uniquement, pas d’appel cloud obligatoire.
- Chiffrement disque conseillé (LUKS/BitLocker) pour environnements sensibles.
- Journalisation locale des requêtes (sans PII).
- Clés de services ou endpoints LLM locaux hors repo (fichier .env, non versionné).
- Avertissement utilisateur visible : pas d’avis juridique.
""",

    "documentation/01-architecture/operations.md": """# Opérations

## Services
- Qdrant local, port 6333.
- Serveur LLM local OpenAI-like (vLLM, llama.cpp wrapper), port configurable.
- FastAPI (uvicorn) pour l’API et l’UI.

## Démarrage
1. Préparer données dans `kaitiaki/data/raw/`.
2. Ingestion : parse → normalize → indexer.
3. Lancer API : `uvicorn kaitiaki.api.server:app --reload`.

## Journalisation
- Logs applicatifs standard.
- `eval/report.json` et `eval/report.csv` pour les campagnes de tests.
""",

    # ========== 02-installation ==========
    "documentation/02-installation/prerequisites.md": """# Prérequis

- OS : Linux/macOS/Windows.
- Python 3.11+.
- Qdrant binaire démarré localement (port 6333).
- Modèle LLM local accessible via API OpenAI-compatible.
- Si CPU uniquement : utiliser un modèle quantisé (GGUF) et limiter max_tokens.
""",

    "documentation/02-installation/quickstart.md": """# Démarrage rapide

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Déposer 6–10 PDF dans kaitiaki/data/raw/
python -m kaitiaki.ingest.parse_pdf
python -m kaitiaki.ingest.normalize
python -m kaitiaki.ingest.indexer

uvicorn kaitiaki.api.server:app --reload
# Ouvrir http://127.0.0.1:8000
````

Pour l’évaluation :

```bash
python -m kaitiaki.eval.evaluate
```

""",

"documentation/02-installation/configuration.md": """# Configuration

Fichier : `kaitiaki/config/app.yaml`

* paths : chemins des données et index BM25.
* qdrant : host, port, collection.
* models :

  * embedding
  * reranker
  * llm\_base\_url
  * llm\_model
* retrieval :

  * top\_k\_dense, top\_k\_bm25, fusion, rerank\_top\_k
    """,

    "documentation/02-installation/run-local.md": """# Exécution locale sans Docker

1. Démarrer Qdrant : binaire ou service.
2. Démarrer le serveur LLM local (OpenAI-like).
3. Créer l’environnement Python, installer requirements.
4. Ingestion des PDF.
5. Lancer FastAPI.

Astuce : pour un poste sans GPU, réduire `rerank_top_k` à 15–20 et `max_tokens` à 400.
""",

# ========== 03-developpement ==========
"documentation/03-developpement/repo-structure.md": """# Arborescence du dépôt

* `kaitiaki/ingest/` : parse\_pdf, normalize, indexer.

* `kaitiaki/rag/` : pipeline hybride, fusion RRF, client LLM, schémas Pydantic.

* `kaitiaki/api/` : serveur FastAPI, templates HTML.

* `kaitiaki/eval/` : tests et métriques.

* `kaitiaki/utils/` : logging, helpers.

* `documentation/` : ce dossier.
  """,

  "documentation/03-developpement/coding-standards.md": """# Conventions de code

* Python 3.11+, typage statique (typing), docstrings Google style.

* Formatage : black, isort, flake8 (optionnel).

* Nommage : snake\_case pour fonctions/variables, PascalCase pour classes.

* Pas de secrets en clair ; variables d’environnement ou fichiers ignorés par Git.
  """,

  "documentation/03-developpement/contributing.md": """# Contribuer

## Workflow

* branche `main` protégée.
* branches de fonctionnalité : `feat/...`, corrections : `fix/...`.
* PR avec description, tests, mise à jour de la doc si nécessaire.
* Revue obligatoire sur PRs significatives.

## Commits

* message clair au présent.
* référence au ticket interne si applicable.

## Releases

* tag sémantique (v0.1.0).
* mise à jour de 07-roadmap/changelog.md.
  """,

  "documentation/03-developpement/api-spec.md": """# Spécification API

## POST /query

Entrée :

```json
{
  "text": "Quelles mesures récentes concernent le BTP ?",
  "sources": ["JONC","IEOM","ISEE"],
  "date_from": "2025-05-01",
  "date_to": "2025-08-25",
  "top_k": 20
}
```

Sortie :

```json
{
  "answer": "Synthèse ...",
  "citations": [
    {"doc_id":"jonc_2025-06-12.pdf","page":4,"snippet":"..."}
  ],
  "latency_ms": 820
}
```

## POST /ingest

* Réindexe les fichiers présents dans `data/raw/`.
* Réponse : `{ "status": "ok" }` ou détails.

## GET /health

* Statut simple `{ "ok": true }`.
  """,

  "documentation/03-developpement/data-ingestion.md": """# Ingestion et indexation

1. `parse_pdf.py` : PDF → `*.pages.json` (page, texte).
2. `normalize.py` : normalise, segmente en chunks → `*.normalized.json`.
3. `indexer.py` :

   * Écrit les chunks dans Qdrant.
   * Encode embeddings denses et met à jour Qdrant.
   * Construit l’index BM25 local (rank-bm25).

Conseils :

* Taille chunk 1 200–1 600, overlap 200–300.

* Ajouter `source`, `date`, `doc_id`, `page` dans metadata.
  """,

  "documentation/03-developpement/tuning-retrieval.md": """# Réglage retrieval

* Augmenter `top_k_dense` et `top_k_bm25` à 40/40 si recall faible.

* Réduire `rerank_top_k` si latence élevée.

* Améliorer le chunking et la qualité de l’OCR.

* Activer OpenSearch en V1.1 pour filtres lexicaux avancés.
  """,

  # ========== 04-tests ==========

  "documentation/04-tests/test-plan.md": """# Plan de tests

## Tests automatisés

* `eval/evaluate.py` :

  * latence p95 end-to-end,
  * recall\@20,
  * taux de citations valides.

## Tests manuels

* Recette UI : saisie requêtes, vérification citations, navigation.
* Robustesse : 50 requêtes variées, mesure erreurs/temps.

## Jeux d’essai

* `eval/qa_testset.json` : 10–15 Q/A couvrant JONC, IEOM, ISEE, délibérations.
  """,

  "documentation/04-tests/evaluation-metrics.md": """# Métriques d’évaluation

* Latence p95 : 95 % des requêtes sous ce temps.

* Recall\@20 : part des références attendues (doc\_id,page) présentes dans les 20 premiers candidats.

* Taux de citations valides : proportion des citations dont le snippet apparaît sur la page référencée.

## Seuils V1

* Latence p95 ≤ 5 000 ms (CPU) ou ≤ 2 500 ms (GPU).

* Recall\@20 ≥ 0,70.

* Citations valides ≥ 0,80.
  """,

  "documentation/04-tests/manual-checklist.md": """# Checklist de recette fonctionnelle

* Saisie d’une question et obtention d’une réponse en français.

* Présence de 2–4 citations avec doc\_id, page, extrait.

* Clic citation → ouverture du document à la page (ou vérification manuelle du texte).

* Filtre source (JONC/IEOM/ISEE/délibérations) fonctionnel.

* Stabilité visuelle et absence d’erreurs console.
  """,

  # ========== 05-operations ==========

  "documentation/05-operations/monitoring.md": """# Observabilité

* Logs applicatifs FastAPI (requêtes, erreurs).

* Journaux de latence et tailles de contextes.

* Exports `eval/report.json` et `eval/report.csv` pour campagnes de test.

* Intégration Prometheus/Grafana possible en V1.1.
  """,

  "documentation/05-operations/backup-restore.md": """# Sauvegarde et restauration

## À sauvegarder

* Qdrant : dossier de stockage (collection Kaitiaki).
* BM25 local : `bm25_index.pkl` et `bm25_meta.json`.
* Données sources : `data/raw/` et `data/processed/`.

## Restauration

1. Restaurer le dossier Qdrant.
2. Remettre les fichiers BM25.
3. Rejouer l’ingestion si nécessaire.
   """,

   "documentation/05-operations/troubleshooting.md": """# Dépannage

## Problèmes de performance

* Réduire `rerank_top_k` et `max_tokens`.
* Vérifier que le LLM local répond dans les délais.

## Résultats médiocres

* Augmenter top\_k\_dense/BM25.
* Ajuster chunking et overlap.
* Qualité OCR insuffisante.

## Erreurs de citations

* Vérifier que les snippets proviennent des passages réellement fournis au LLM.

* Augmenter la longueur minimale des snippets.
  """,

  # ========== 06-legal ==========

  "documentation/06-legal/licenses.md": """# Licences

* Bibliothèques Python : se référer au fichier `requirements.txt`.

* Modèles : vérifier les licences des modèles utilisés (embeddings, reranker, LLM).

* Données : les publications publiques restent la propriété des émetteurs ; respecter les conditions d’utilisation.
  """,

  # ========== 07-roadmap ==========

  "documentation/07-roadmap/roadmap.md": """# Roadmap

## V1 (MVP)

* RAG hybride local (Qdrant + BM25 local).
* UI minimaliste, citations cliquables.
* Évaluation basique et seuils de sortie.

## V1.1

* OpenSearch pour BM25 avancé et filtres par champs.
* Alertes hebdomadaires par email.

## V2

* Intégration opendata (indicateurs avec graphiques).
* Filtres thématiques et taxonomie.
* Authentification basique.

## V3

* Graphe de connaissances ciblé.
* Ontologie restreinte pour explicabilité.
  """,

  "documentation/07-roadmap/changelog.md": """# Changelog

## \[Unreleased]

* Initialisation de la documentation.

## v0.1.0 - MVP

* Ingestion PDF, indexation Qdrant + BM25 local.

* Pipeline RAG hybride + reranking.

* API FastAPI et UI simple.

* Évaluation et checklist V1.
  """,

  # ========== 08-branding ==========

  "documentation/08-branding/naming.md": """# Naming

* Nom produit : **Kaitiaki**

* Sens : gardien, protecteur, veilleur.

* Variantes dépôt :

  * `kaitiaki`
  * `kaitiaki-nc`
    """,

    "documentation/08-branding/ui-copy.md": """# UI Copy

* Titre : Kaitiaki — Veille NC

* Champ de recherche : "Saisissez votre question"

* Bouton : "Chercher"

* Avertissement : "Kaitiaki fournit des synthèses d’informations publiques. Ce n’est pas un avis juridique."

* Messages d’erreur : "Aucune source trouvée pour cette requête", "Temps de réponse dépassé"
  """,
  }

def main() -> None:
    parser = argparse.ArgumentParser(description="Génère l’arborescence documentation/ pour Kaitiaki.")
    parser.add_argument("--force", action="store_true", help="Écrase les fichiers existants.")
    args = parser.parse_args()

    created, skipped, overwritten = 0, 0, 0

    for rel_path, content in FILES.items():
        out_path = ROOT / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.exists() and not args.force:
            skipped += 1
            continue
        if out_path.exists() and args.force:
            overwritten += 1
        else:
            created += 1
        out_path.write_text(content, encoding="utf-8")

    print(f"Documentation générée sous: {DOC}")
    print(f"Créés: {created}  |  Ignorés: {skipped}  |  Écrasés: {overwritten}")

if __name__ == "main":
    main()