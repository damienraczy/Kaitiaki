# Ingestion et indexation

1. `parse_pdf.py` : PDF → `*.pages.json` (page, texte).
2. `normalize.py` : normalise, segmente en chunks → `*.normalized.json`.
3. `indexer.py` :

   * Écrit les chunks dans Qdrant.
   * Encode embeddings denses et met à jour Qdrant.
   * Construit l’index BM25 local (rank-bm25).

Conseils :

* Taille chunk 1 200–1 600, overlap 200–300.

* Ajouter `source`, `date`, `doc_id`, `page` dans metadata.
  