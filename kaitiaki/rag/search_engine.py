# kaitiaki/rag/search_engine.py
import time
import json
import pickle
from pathlib import Path
from typing import List, Tuple, Dict

import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from haystack import Document
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from .fusion import rrf_merge
from kaitiaki.utils.settings import CFG

def _bm25_search(query: str, top_k: int, bm25_index: Dict) -> List[Tuple[int, float]]:
    """Effectue une recherche BM25 en utilisant un index pré-chargé."""
    bm25 = bm25_index["bm25"]
    toks = [t for t in query.lower().split() if len(t) > 2]
    scores = bm25.get_scores(toks)
    idx = np.argsort(scores)[::-1][:top_k]
    return [(int(i), float(scores[i])) for i in idx]

def _dense_search(query: str, top_k: int, retriever: QdrantEmbeddingRetriever, embedder: SentenceTransformer) -> List[Document]:
    """Effectue une recherche dense en utilisant des composants pré-chargés."""
    query_embedding = embedder.encode(query, normalize_embeddings=True)
    retrieval_results = retriever.run(query_embedding=query_embedding.tolist(), top_k=top_k)
    return retrieval_results.get("documents", [])

def hybrid_search(
    q: str,
    models: dict,
    top_k_dense: int = 20,
    top_k_bm25: int = 20,
    rerank_top_k: int = 25
) -> Tuple[List[Tuple[Document, float]], int]:
    t0 = time.time()

    store = models["store"]
    retriever = models["retriever"]
    embedder = models["embedder"]
    reranker = models["reranker"]
    bm25_index = models["bm25_index"]

    dense_docs = _dense_search(q, top_k_dense, retriever, embedder)

    bm25_docs = []
    bm25_results = _bm25_search(q, top_k_bm25, bm25_index)
    if bm25_results:
        bm25_meta_list = bm25_index["meta"]
        for i, score in bm25_results:
            meta = bm25_meta_list[i]
            
            # --- CORRECTION DE LA SYNTAXE DU FILTRE ---
            filters = {
                "operator": "AND",
                "conditions": [
                    {"field": "meta.doc_id", "operator": "==", "value": meta["doc_id"]},
                    {"field": "meta.page", "operator": "==", "value": meta["page"]},
                ],
            }
            # --- FIN DE LA CORRECTION ---
            
            hits = store.filter_documents(filters=filters)
            if hits:
                bm25_docs.extend(hits)

    def key(d: Document): 
        return f'{d.meta.get("doc_id")}#p{d.meta.get("page")}#{hash(d.content)}'

    all_docs = {key(d): d for d in dense_docs + bm25_docs}
    dense_keys_with_scores = [(key(d), 1.0) for d in dense_docs] # Score factice pour RRF
    bm25_keys_with_scores = []
    if bm25_results:
        bm25_meta_list = bm25_index["meta"]
        # Trouver le document correspondant pour chaque résultat BM25
        for i, score in bm25_results:
             meta = bm25_meta_list[i]
             # Cette recherche est simpliste, une meilleure approche utiliserait un ID unique par chunk
             for doc in bm25_docs:
                 if doc.meta.get("doc_id") == meta["doc_id"] and doc.meta.get("page") == meta["page"]:
                     bm25_keys_with_scores.append((key(doc), score))
                     break
    
    fused_ids = [k for k, _ in rrf_merge(dense_keys_with_scores, bm25_keys_with_scores)]
    candidates = [all_docs[id_] for id_ in fused_ids if id_ in all_docs][:rerank_top_k]

    if not candidates:
        return [], int((time.time() - t0) * 1000)
        
    pairs = [(q, doc.content) for doc in candidates]
    scores = reranker.predict(pairs)
    
    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    
    latency = int((time.time() - t0) * 1000)
    return ranked, latency