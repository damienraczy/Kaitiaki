# Sauvegarde et restauration

## À sauvegarder

* Qdrant : dossier de stockage (index Kaitiaki).
* BM25 local : `bm25_index.pkl` et `bm25_meta.json`.
* Données sources : `data/raw/` et `data/processed/`.

## Restauration

1. Restaurer le dossier Qdrant.
2. Remettre les fichiers BM25.
3. Rejouer l’ingestion si nécessaire.
   