# Modèle de données

## Fichiers intermédiaires
- `*.pages.json` :
  - doc_id, pages[{page:int, text:str}]
- `*.normalized.json` :
  - doc_id, date, chunks[{doc_id, date, page, text, source}]

## Indices
- Qdrant : documents = chunks, metadata = {doc_id, page, date, source}, embedding 384-d.
- BM25 local : tokenisation simple FR/EN, fichiers `bm25_index.pkl`, `bm25_meta.json`.

## API
- POST /query : {text, sources?, date_from?, date_to?, top_k?}
- Réponse : {answer, citations[], latency_ms}
