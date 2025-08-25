# Configuration

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
    