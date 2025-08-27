# kaitiaki/rag/pipeline.py
import time
import json
import pickle
from pathlib import Path
from typing import List, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from haystack import Document
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from .fusion import rrf_merge

from kaitiaki.utils.settings import CFG

# CFG = yaml.safe_load((Path(__file__).resolve().parents[1] / "config" / "app.yaml").read_text(encoding="utf-8"))

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

def _dense_search(store: QdrantDocumentStore, embedder: SentenceTransformer, query: str, top_k: int):
    q = embedder.encode([query], normalize_embeddings=True)[0]
    # docs: List[Document] = store.query_by_embedding(q, top_k=top_k)
    docs: List[Document] = store._query_by_embedding(q, top_k=top_k)
    return docs

def hybrid_search(query: str, top_k_dense=20, top_k_bm25=20, rerank_top_k=25):
    t0 = time.time()
    # 1) stores / modèles
    store = QdrantDocumentStore(
        host=CFG["qdrant"]["host"],
        port=CFG["qdrant"]["port"],
        # collection_name=CFG["qdrant"]["collection"],
        index=CFG["qdrant"]["collection"],
        embedding_dim=384,
    )
    embedder = SentenceTransformer(CFG["models"]["embedding"])
    reranker = CrossEncoder(CFG["models"]["reranker"])

    # 2) dense + bm25
    dense_docs = _dense_search(store, embedder, query, top_k_dense)
    bm25_list = _bm25_search(query, top_k_bm25)     # [(idx, score)]
    bm25_meta = json.loads(Path(CFG["paths"]["bm25_meta"]).read_text(encoding="utf-8"))

    # Pour BM25: on ne stocke pas le texte; on reconstruit des "pseudo-docs" minimalistes
    bm25_docs = []
    for i, sc in bm25_list:
        m = bm25_meta[i]
        # Récupérer le chunk depuis Qdrant par filtre meta (doc_id + page)
        # filters={"doc_id": m["doc_id"], "page": m["page"]}
        filters = {
            "operator": "AND",
            "conditions": [
                {"field": "meta.doc_id", "operator": "==", "value": m["doc_id"]},
                {"field": "meta.page", "operator": "==", "value": m["page"]},
            ],
        }

        hits = store.filter_documents(filters=filters)
        if hits:
            bm25_docs.append(hits[0])

    # 3) Fusion RRF (sur identifiants)
    def key(d: Document): 
        return f'{d.meta.get("doc_id")}#p{d.meta.get("page")}#{hash(d.content)}'

    dense_pairs = [(key(d), 1.0) for d in dense_docs]
    bm25_pairs  = [(key(d), 1.0) for d in bm25_docs]
    fused_ids = [k for k,_ in rrf_merge(dense_pairs, bm25_pairs)]

    # Limiter pour reranking
    id_to_doc = {key(d): d for d in (dense_docs + bm25_docs)}
    candidates = [id_to_doc[i] for i in fused_ids if i in id_to_doc][:rerank_top_k]

    # 4) Rerank (cross-encoder)
    pairs = [(query, d.content) for d in candidates]
    scores = reranker.predict(pairs)
    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)

    latency = int((time.time() - t0) * 1000)
    return ranked, latency
