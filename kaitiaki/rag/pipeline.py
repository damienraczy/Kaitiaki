# kaitiaki/rag/pipeline.py
import time
import json
import pickle
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from haystack import Document
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from .fusion import rrf_merge

from kaitiaki.utils.settings import CFG
from kaitiaki.utils.logging import logger

# --- Initialisation des composants (chargés une seule fois) ---
embedder = None
reranker = None
store = None
retriever = None
bm25_cache = None

def initialize_components():
    """Initialize components lazily"""
    global embedder, reranker, store, retriever
    
    if embedder is None:
        logger.info("Initializing sentence transformer...")
        embedder = SentenceTransformer(CFG["embedding"]["model"])
        
    if reranker is None:
        logger.info("Initializing cross-encoder...")
        reranker = CrossEncoder(CFG["reranker"]["model"])
        
    if store is None:
        logger.info("Initializing Qdrant document store...")
        embedding_dimension = embedder.get_sentence_embedding_dimension()
        store = QdrantDocumentStore(
            host=CFG["qdrant"]["host"],
            port=CFG["qdrant"]["port"],
            index=CFG["qdrant"]["index"],
            embedding_dim=embedding_dimension,
        )
        
    if retriever is None:
        logger.info("Initializing Qdrant retriever...")
        retriever = QdrantEmbeddingRetriever(document_store=store)

def _load_bm25():
    """Load BM25 index with caching and error handling"""
    global bm25_cache
    
    if bm25_cache is not None:
        return bm25_cache
        
    bm25_path = Path(CFG["paths"]["bm25_index"])
    bm25_meta_path = Path(CFG["paths"]["bm25_meta"])
    
    if not bm25_path.exists():
        logger.warning(f"BM25 index not found at {bm25_path}")
        logger.info("BM25 search will be skipped. Run indexer first: python -m kaitiaki.ingest.indexer")
        return None, None, None
        
    if not bm25_meta_path.exists():
        logger.warning(f"BM25 metadata not found at {bm25_meta_path}")
        return None, None, None
    
    try:
        with open(bm25_path, "rb") as f:
            pk = pickle.load(f)
        meta = json.loads(bm25_meta_path.read_text(encoding="utf-8"))
        
        bm25_cache = (pk["bm25"], pk["tokenized"], meta)
        logger.info(f"BM25 index loaded successfully ({len(meta)} documents)")
        return bm25_cache
        
    except Exception as e:
        logger.error(f"Error loading BM25 index: {e}")
        return None, None, None

def _bm25_search(query: str, top_k: int) -> List[Tuple[int, float]]:
    """BM25 search with error handling"""
    try:
        bm25, tokenized, meta = _load_bm25()
        
        if bm25 is None:
            logger.warning("BM25 search skipped - index not available")
            return []
            
        toks = [t for t in query.lower().split() if len(t) > 2]
        if not toks:
            logger.warning("No valid tokens for BM25 search")
            return []
            
        scores = bm25.get_scores(toks)
        idx = np.argsort(scores)[::-1][:top_k]
        
        # Filter out zero scores
        results = [(int(i), float(scores[i])) for i in idx if scores[i] > 0]
        logger.debug(f"BM25 search returned {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Error in BM25 search: {e}")
        return []

def _dense_search(query: str, top_k: int) -> List[Document]:
    """Dense search with error handling"""
    try:
        initialize_components()
        
        query_embedding = embedder.encode(query, normalize_embeddings=True)
        retrieval_results = retriever.run(query_embedding=query_embedding.tolist(), top_k=top_k)
        
        documents = retrieval_results.get("documents", [])
        logger.debug(f"Dense search returned {len(documents)} results")
        return documents
        
    except Exception as e:
        logger.error(f"Error in dense search: {e}")
        return []

def hybrid_search(q: str, top_k: int = 20) -> Tuple[List[Tuple[Document, float]], int]:
    """Hybrid search with robust error handling"""
    t0 = time.time()
    
    try:
        initialize_components()
        
        # 1) Dense search (always try this first)
        dense_docs = _dense_search(q, top_k=top_k)
        
        # 2) BM25 search (fallback gracefully if not available)
        bm25_list = _bm25_search(q, top_k=top_k)
        
        # 3) Get BM25 documents if we have results
        bm25_docs = []
        if bm25_list:
            try:
                _, _, bm25_meta = _load_bm25()
                if bm25_meta:
                    for i, sc in bm25_list:
                        if i < len(bm25_meta):
                            meta = bm25_meta[i]
                            filters = {
                                "operator": "AND",
                                "conditions": [
                                    {"field": "meta.doc_id", "operator": "==", "value": meta["doc_id"]},
                                    {"field": "meta.page", "operator": "==", "value": meta["page"]},
                                ],
                            }
                            hits = store.filter_documents(filters=filters)
                            if hits:
                                bm25_docs.append(hits[0])
            except Exception as e:
                logger.warning(f"Error retrieving BM25 documents: {e}")
        
        # 4) Combine results
        if not dense_docs and not bm25_docs:
            logger.warning(f"No search results found for query: {q}")
            return [], int((time.time() - t0) * 1000)
        
        # Use fusion if we have both types of results
        if dense_docs and bm25_docs:
            logger.debug("Using hybrid fusion")
            def key(d: Document): 
                return f'{d.meta.get("doc_id")}#p{d.meta.get("page")}#{hash(d.content)}'

            all_docs = {key(d): d for d in dense_docs + bm25_docs}
            dense_keys = [key(d) for d in dense_docs]
            bm25_keys = [key(d) for d in bm25_docs]
            
            fused_ids = [k for k, _ in rrf_merge([(k, 1.0) for k in dense_keys], [(k, 1.0) for k in bm25_keys])]
            candidates = [all_docs[id_] for id_ in fused_ids if id_ in all_docs]
        else:
            # Use whichever we have
            candidates = dense_docs if dense_docs else bm25_docs
            logger.debug(f"Using {'dense' if dense_docs else 'BM25'} search only")
        
        if not candidates:
            return [], int((time.time() - t0) * 1000)
        
        # 5) Reranking
        try:
            pairs = [(q, doc.content) for doc in candidates]
            scores = reranker.predict(pairs)
            ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        except Exception as e:
            logger.warning(f"Reranking failed, using original order: {e}")
            # Fallback: return documents with dummy scores
            ranked = [(doc, 1.0) for doc in candidates]
        
        latency = int((time.time() - t0) * 1000)
        logger.info(f"Hybrid search completed in {latency}ms, returned {len(ranked)} results")
        
        return ranked, latency
        
    except Exception as e:
        latency = int((time.time() - t0) * 1000)
        logger.error(f"Critical error in hybrid_search: {e}")
        return [], latency