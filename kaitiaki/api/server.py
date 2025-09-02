# kaitiaki/api/server.py
import time
from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import pickle
import json
from threading import Lock

# Imports pour le chargement des modèles
from kaitiaki.rag.search_engine import hybrid_search
from kaitiaki.rag.llm_client import generate_answer
from kaitiaki.rag.schemas import Answer, Query, Latency, Citation
from kaitiaki.utils.logging import logger
from kaitiaki.utils.settings import CFG
from sentence_transformers import SentenceTransformer, CrossEncoder
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from kaitiaki.ingest import parse_pdf, normalize, indexer

MODELS = {}
INGESTION_LOCK = Lock()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Chargement des modèles et des index...")
    
    MODELS["embedder"] = SentenceTransformer(CFG["embedding"]["model"])
    MODELS["reranker"] = CrossEncoder(CFG["reranker"]["model"])
    
    embedding_dim = MODELS["embedder"].get_sentence_embedding_dimension()
    store = QdrantDocumentStore(
        host=CFG["qdrant"]["host"],
        port=CFG["qdrant"]["port"],
        index=CFG["qdrant"]["index"],
        embedding_dim=embedding_dim,
    )
    MODELS["store"] = store
    MODELS["retriever"] = QdrantEmbeddingRetriever(document_store=store)
    
    with open(CFG["paths"]["bm25_index"], "rb") as f:
        bm25_data = pickle.load(f)
    meta = json.loads(Path(CFG["paths"]["bm25_meta"]).read_text(encoding="utf-8"))
    MODELS["bm25_index"] = {
        "bm25": bm25_data["bm25"],
        "tokenized": bm25_data["tokenized"],
        "meta": meta
    }
    
    logger.info("Tous les modèles et index ont été chargés.")
    yield
    MODELS.clear()

app = FastAPI(
    title="Kaitiaki API",
    description="API pour le moteur de recherche RAG Kaitiaki.",
    version="0.1.0",
    lifespan=lifespan
)

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ingest")
async def ingest_documents():
    if not INGESTION_LOCK.acquire(blocking=False):
        return {"status": "busy", "message": "Une ingestion est déjà en cours."}
    try:
        logger.info("Début de l'ingestion via API...")
        parse_pdf.main()
        normalize.main()
        indexer.main()
        logger.info("Ingestion terminée avec succès.")
        return {"status": "ok", "message": "Les documents ont été ingérés."}
    except Exception as e:
        logger.error(f"Erreur durant l'ingestion via API : {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
    finally:
        INGESTION_LOCK.release()

@app.post("/query", response_model=Answer)
async def query_endpoint(query: Query):
    start_time = time.time()
    
    ranked_results, retrieval_latency_ms = hybrid_search(
        query.question,
        models=MODELS,
        top_k_dense=CFG["retrieval"]["top_k_dense"],
        top_k_bm25=CFG["retrieval"]["top_k_bm25"],
        rerank_top_k=CFG["retrieval"]["rerank_top_k"]
    )
    
    contexts = [doc.content for doc, score in ranked_results[:8]]
    
    llm_start = time.time()
    generated_answer = generate_answer(query.question, contexts)
    llm_end = time.time()
    
    total_latency_ms = int((time.time() - start_time) * 1000)
    llm_latency_ms = int((llm_end - llm_start) * 1000)
    
    latency_details = Latency(
        total_ms=total_latency_ms,
        retrieval_ms=retrieval_latency_ms,
        llm_ms=llm_latency_ms
    )
    
    citations = [
        Citation(
            document_id=doc.meta.get("doc_id", "ID inconnu"),
            content=doc.content,
            page_number=doc.meta.get("page", 0),
            source=doc.meta.get("source", "Source inconnue")
        ) for doc, score in ranked_results[:5]
    ]

    return Answer(
        answer=generated_answer,
        citations=citations,
        latency=latency_details
    )

@app.post("/search", response_class=HTMLResponse)
async def search(request: Request, question: str = Form(...)):
    query_obj = Query(question=question)
    response = await query_endpoint(query_obj)
    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "q": question,
            "answer": response.answer,
            "cits": response.citations,
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)