## 1) README.md

````markdown
# Kaitiaki — Veille stratégique NC (MVP)

Assistant de veille pour interroger et synthétiser des publications publiques (JONC, IEOM, ISEE, délibérations).

## Objectif MVP
- Corpus limité (6–10 PDF récents).
- RAG hybride **sans Docker** : 
  - dense (Qdrant + embeddings),
  - lexical (BM25 local via `rank-bm25`),
  - fusion RRF,
  - reranking (cross-encoder),
  - génération via LLM local (7–8B recommandé).

## Prérequis
- macOS / Linux / Windows
- Python 3.11+
- Qdrant **binaire** (server) lancé localement (par défaut : `127.0.0.1:6333`)
- Modèle LLM local (ex. Llama 3.1 / Mistral) servi en API compatible OpenAI (ex. `vLLM`) **ou** `llama.cpp` + petit wrapper HTTP.

## Installation
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
````

## Config

Éditez `kaitiaki/config/app.yaml` :

* chemins,
* nom de collection Qdrant,
* modèles (embedding, reranker, LLM),
* paramètres retrieval.

## Données

Déposez 6–10 PDF dans `kaitiaki/data/raw/`.

## Pipeline d’ingestion

```bash
python -m kaitiaki.ingest.parse_pdf
python -m kaitiaki.ingest.normalize
python -m kaitiaki.ingest.indexer
```

## Lancer l’API

```bash
uvicorn kaitiaki.api.server:app --reload
```

Ouvrez [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Endpoints

* `POST /ingest` : (ré)indexation des fichiers présents.
* `POST /query` : { "text": "...", "from": "2025-05-01", "to": "2025-08-25", "sources": \["JONC","IEOM","ISEE"] }
* `GET /health`

## Notes

* BM25 est implémenté localement via `rank-bm25` (pickle). Pour des filtres lexicaux avancés, vous pourrez **ajouter OpenSearch** en V1.1 sans changer l’API.
* Le LLM local doit exposer une route OpenAI-compatible (`/v1/chat/completions`).

## Licence / Avertissement

Kaitiaki fournit des synthèses d’informations publiques. **Ce n’est pas un avis juridique.**

````

