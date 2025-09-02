# Réglage retrieval

* Augmenter `top_k_dense` et `top_k_bm25` à 40/40 si recall faible.

* Réduire `rerank_top_k` si latence élevée.

* Améliorer le chunking et la qualité de l’OCR.

* Activer OpenSearch en V1.1 pour filtres lexicaux avancés.
  