# kaitiaki/rag/search_engine.py
import time
import json
from typing import List, Tuple, Dict

import numpy as np
from sentence_transformers import SentenceTransformer
from haystack import Document
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from .fusion import rrf_merge
from kaitiaki.utils.settings import CFG
from kaitiaki.utils.logging import logger

def _bm25_search(query: str, top_k: int, bm25_index: Dict) -> List[Tuple[str, float]]:
    """
    Effectue une recherche BM25 sur l'index des chunks enfants.
    Retourne une liste de (chunk_id, score).
    """
    bm25 = bm25_index["bm25"]
    meta = bm25_index["meta"]
    toks = [t for t in query.lower().split() if len(t) > 2]
    scores = bm25.get_scores(toks)
    idx = np.argsort(scores)[::-1][:top_k]
    return [(meta[i]["chunk_id"], float(scores[i])) for i in idx if "chunk_id" in meta[i]]

def _dense_search(query: str, top_k: int, retriever: QdrantEmbeddingRetriever, embedder: SentenceTransformer) -> List[Document]:
    """
    Effectue une recherche vectorielle dense en filtrant exclusivement
    sur les chunks de type "child".
    """
    query_embedding = embedder.encode(query, normalize_embeddings=True)
    
    # Filtre crucial pour ne chercher que parmi les chunks "enfants"
    filters = {"field": "meta.chunk_type", "operator": "==", "value": "child"}
    
    retrieval_results = retriever.run(
        query_embedding=query_embedding.tolist(),
        filters=filters,
        top_k=top_k
    )
    return retrieval_results.get("documents", [])

def hybrid_search(
    q: str,
    models: dict,
    top_k_dense: int = 20,
    top_k_bm25: int = 20,
    rerank_top_k: int = 25
) -> Tuple[List[Document], List[Document], int]:
    """
    Implémente la stratégie de recherche hybride "parent/child".
    1. Recherche et fusionne les chunks "enfants" les plus pertinents.
    2. Reranke ces "enfants" pour une précision maximale.
    3. Récupère les "parents" correspondants pour un contexte riche.
    
    Retourne:
        - parent_docs_for_context (List[Document]): Les chunks parents pour le LLM.
        - top_children_for_citation (List[Document]): Les chunks enfants pour les citations.
        - latency (int): La latence totale de la recherche en ms.
    """
    t0 = time.time()

    retriever = models["retriever"]
    embedder = models["embedder"]
    reranker = models["reranker"]
    bm25_index = models["bm25_index"]
    store = models["store"]

    # --- Étape 1 : Recherche initiale sur les chunks "enfants" ---
    dense_docs = _dense_search(q, top_k_dense, retriever, embedder)
    
    bm25_docs = []
    bm25_results = _bm25_search(q, top_k_bm25, bm25_index)
    if bm25_results:
        bm25_chunk_ids = [chunk_id for chunk_id, score in bm25_results]
        filters = {
            "operator": "AND",
            "conditions": [
                {"field": "meta.chunk_id", "operator": "in", "value": bm25_chunk_ids},
                {"field": "meta.chunk_type", "operator": "==", "value": "child"}
            ]
        }
        bm25_docs = store.filter_documents(filters=filters)

    # Fusion des résultats enfants
    def key(d: Document): return d.meta.get("chunk_id")
    all_children = {key(d): d for d in dense_docs + bm25_docs if key(d)}
    
    dense_keys = [(key(d), 1.0) for d in dense_docs if key(d)] # Score factice pour RRF
    bm25_keys = bm25_results
    
    fused_ids = [k for k, _ in rrf_merge(dense_keys, bm25_keys)]
    candidates = [all_children.get(id_) for id_ in fused_ids if all_children.get(id_) is not None][:rerank_top_k]

    if not candidates:
        return [], [], int((time.time() - t0) * 1000)
        
    # --- Étape 2 : Reranking des chunks "enfants" pour identifier les plus pertinents ---
    pairs = [(q, doc.content) for doc in candidates]
    scores = reranker.predict(pairs)
    
    ranked_children = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    
    # --- Étape 3 : Récupération des chunks "parents" pour le contexte ---
    # On garde les 5 meilleurs enfants pour les citations et pour trouver les parents.
    top_children_for_citation = [doc for doc, score in ranked_children[:5]]
    
    # Extraire les IDs des parents uniques à partir des meilleurs enfants.
    parent_ids_to_fetch = list(set(
        c.meta.get("parent_id") for c in top_children_for_citation if c.meta.get("parent_id")
    ))

    if not parent_ids_to_fetch:
        logger.warning("Aucun parent_id trouvé pour les meilleurs enfants. Le contexte sera peut-être limité.")
        # Cas de repli : on retourne les enfants eux-mêmes comme contexte.
        return top_children_for_citation, top_children_for_citation, int((time.time() - t0) * 1000)

    # Récupérer les documents parents complets depuis Qdrant.
    parent_filters = {
        "operator": "AND",
        "conditions": [
            {"field": "meta.chunk_id", "operator": "in", "value": parent_ids_to_fetch},
            {"field": "meta.chunk_type", "operator": "==", "value": "parent"}
        ]
    }
    parent_docs_for_context = store.filter_documents(filters=parent_filters)

    latency = int((time.time() - t0) * 1000)
    
    logger.info(f"Recherche effectuée en {latency}ms. {len(parent_docs_for_context)} chunks parents trouvés pour le contexte.")
    
    return parent_docs_for_context, top_children_for_citation, latency

