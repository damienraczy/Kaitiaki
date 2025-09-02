# Architecture technique

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
