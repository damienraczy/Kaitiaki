# kaitiaki/rag/retriever.py
import time
import json
import pickle
from pathlib import Path
from typing import List, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from haystack import Document
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from .fusion import rrf_merge

from kaitiaki.utils.settings import CFG

# --- Initialisation des composants (chargés une seule fois) ---
embedder = SentenceTransformer(CFG["embedding"]["model"])
reranker = CrossEncoder(CFG["reranker"]["model"])
embedding_dimension = embedder.get_sentence_embedding_dimension()
print(f"Dimension de l'embedding détectée : {embedding_dimension}")

store = QdrantDocumentStore(
    host=CFG["qdrant"]["host"],
    port=CFG["qdrant"]["port"],
    index=CFG["qdrant"]["index"],
    embedding_dim=embedding_dimension,
)

# --- CORRECTION 2 : Initialiser le Retriever en lui passant le store ---
retriever = QdrantEmbeddingRetriever(document_store=store)


def _load_bm25():
    with open(CFG["paths"]["bm25_index"], "rb") as f:
        pk = pickle.load(f)
    meta = json.loads(Path(CFG["paths"]["bm25_meta"]).read_text(encoding="utf-8"))
    return pk["bm25"], pk["tokenized"], meta

def _bm25_search(query: str, top_k: int) -> List[Tuple[int, float]]:
    bm25, tokenized, meta = _load_bm25()
    toks = [t for t in query.lower().split() if len(t) > 2]
    scores = bm25.get_scores(toks)
    idx = np.argsort(scores)[::-1][:top_k]
    return [(int(i), float(scores[i])) for i in idx]

def _dense_search(query: str, top_k: int) -> List[Document]:
    query_embedding = embedder.encode(query, normalize_embeddings=True)
    
    # --- CORRECTION 3 : Utiliser le retriever.run() ---
    # La méthode run() du retriever exécute la recherche
    retrieval_results = retriever.run(query_embedding=query_embedding.tolist(), top_k=top_k)
    
    # Le retriever retourne un dictionnaire, les documents sont dans la clé "documents"
    return retrieval_results.get("documents", [])


def hybrid_search(q: str, top_k: int = 20) -> Tuple[List[Tuple[Document, float]], int]:
    t0 = time.time()

    # 1) Recherche Dense (vectorielle)
    dense_docs = _dense_search(q, top_k=top_k)
    bm25_list = _bm25_search(q, top_k=top_k)

    # 2) Recherche Lexicale (BM25) et récupération du contenu
    bm25_docs = []
    if bm25_list:
        bm25_meta = json.loads(Path(CFG["paths"]["bm25_meta"]).read_text(encoding="utf-8"))
        for i, sc in bm25_list:
            meta = bm25_meta[i]
            filters = {
                "operator": "AND",
                "conditions": [
                    {"field": "meta.doc_id", "operator": "==", "value": meta["doc_id"]},
                    {"field": "meta.page", "operator": "==", "value": meta["page"]},
                ],
            }
            # Utiliser filter_documents, qui est conçu pour ce genre de requêtes
            hits = store.filter_documents(filters=filters)
            if hits:
                bm25_docs.append(hits[0])

    # 3) Fusion et Reranking
    def key(d: Document): 
        return f'{d.meta.get("doc_id")}#p{d.meta.get("page")}#{hash(d.content)}'

    all_docs = {key(d): d for d in dense_docs + bm25_docs}
    dense_keys = [key(d) for d in dense_docs]
    bm25_keys = [key(d) for d in bm25_docs]
    
    fused_ids = [k for k, _ in rrf_merge([(k, 1.0) for k in dense_keys], [(k, 1.0) for k in bm25_keys])]
    candidates = [all_docs[id_] for id_ in fused_ids if id_ in all_docs]

    if not candidates:
        return [], int((time.time() - t0) * 1000)
        
    pairs = [(q, doc.content) for doc in candidates]
    scores = reranker.predict(pairs)
    
    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    
    latency = int((time.time() - t0) * 1000)
    return ranked, latency