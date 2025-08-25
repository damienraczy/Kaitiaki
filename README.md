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
