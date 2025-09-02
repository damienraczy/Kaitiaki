import time
from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from kaitiaki.rag.retriever import hybrid_search
from kaitiaki.rag.llm_client import generate_answer
from kaitiaki.rag.schemas import Answer, Query, Latency, Citation
from kaitiaki.utils.logging import logger

# Initialisation de l'application FastAPI
app = FastAPI(
    title="Kaitiaki API",
    description="API pour le moteur de recherche RAG Kaitiaki.",
    version="0.1.0",
)

# Configuration des templates Jinja2
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Affiche la page d'accueil avec le formulaire de recherche."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/query", response_model=Answer)
async def query_endpoint(query: Query):
    """Traite une question et retourne une réponse structurée."""
    start_time = time.time()
    
    # Exécution du search_engine
    ranked_results, retrieval_latency_ms = hybrid_search(query.question)
    
    # Préparation du contexte pour le LLM
    contexts = [doc.content for doc, score in ranked_results[:8]]
    
    # --- CORRECTION : Appel réel au LLM ---
    llm_start = time.time()
    generated_answer = generate_answer(query.question, contexts)
    llm_end = time.time()
    
    # Calcul des latences
    total_latency_ms = int((time.time() - start_time) * 1000)
    llm_latency_ms = int((llm_end - llm_start) * 1000)
    
    latency_details = Latency(
        total_ms=total_latency_ms,
        retrieval_ms=retrieval_latency_ms,
        llm_ms=llm_latency_ms
    )
    
    # Formatage des citations selon le nouveau schéma
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
    """(Endpoint déprécié, utilisé par l'ancien formulaire) Gère la soumission du formulaire et affiche les résultats."""
    query_obj = Query(question=question)
    response = await query_endpoint(query_obj)
    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "q": question, # le template result.html attend 'q'
            "answer": response.answer,
            "cits": response.citations, # le template result.html attend 'cits'
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)