# Opérations

## Services
- Qdrant local, port 6333.
- Serveur LLM local OpenAI-like (vLLM, llama.cpp wrapper), port configurable.
- FastAPI (uvicorn) pour l’API et l’UI.

## Démarrage
1. Préparer données dans `kaitiaki/data/raw/`.
2. Ingestion : parse → normalize → indexer.
3. Lancer API : `uvicorn kaitiaki.api.server:app --reload`.

## Journalisation
- Logs applicatifs standard.
- `eval/report.json` et `eval/report.csv` pour les campagnes de tests.
