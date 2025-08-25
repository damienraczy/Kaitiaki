# Pipeline RAG hybride

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
