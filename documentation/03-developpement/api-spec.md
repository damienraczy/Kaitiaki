# Spécification API

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
  