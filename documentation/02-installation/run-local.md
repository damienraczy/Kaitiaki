# Exécution locale sans Docker

1. Démarrer Qdrant : binaire ou service.
2. Démarrer le serveur LLM local (OpenAI-like).
3. Créer l’environnement Python, installer requirements.
4. Ingestion des PDF.
5. Lancer FastAPI.

Astuce : pour un poste sans GPU, réduire `rerank_top_k` à 15–20 et `max_tokens` à 400.
