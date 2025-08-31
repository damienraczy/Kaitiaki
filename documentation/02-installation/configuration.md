# Configuration

Fichier : `kaitiaki/config/app.yaml`

* paths : chemins des données et index BM25.
* qdrant : host, port, index.
* models :

  * embedding
  * reranker
  * llm_base_url
  * llm_model
* retrieval :

  * top_k_dense, top_k_bm25, fusion, rerank_top_k
