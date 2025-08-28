# kaitiaki/api/server.py
import time
from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from kaitiaki.rag.pipeline import hybrid_search
from kaitiaki.rag.llm_client import generate_answer
from kaitiaki.rag.schemas import Answer, Query, Latency, Citation
from kaitiaki.utils.settings import CFG
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
    
    # Exécution du pipeline de recherche
    ranked_results, retrieval_latency_ms = hybrid_search(query.question)


    # Simulation de la génération de la réponse par le LLM
    llm_start = time.time()
    time.sleep(0.5)  # Simule le temps de génération
    generated_answer = f"Réponse générée pour la question : '{query.question}'"
    llm_end = time.time()
    
    end_time = time.time()

    # Calcul des latences
    total_latency_ms = int((end_time - start_time) * 1000)
    llm_latency_ms = int((llm_end - llm_start) * 1000)
    
    latency_details = Latency(
        total_ms=total_latency_ms,
        retrieval_ms=retrieval_latency_ms, # On utilise la valeur précise du pipeline
        llm_ms=llm_latency_ms
    )
    
    citations = [
        Citation(
            document_id=doc.meta.get("doc_id", "ID inconnu"),
            content=doc.content,
            page_number=doc.meta.get("page", 0),
            source=doc.meta.get("source", "Source inconnue")
        ) for doc, score in ranked_results[:5] # On limite aux 5 meilleures citations
    ]

    return Answer(
        answer=generated_answer,
        citations=citations,
        latency=latency_details
    )

@app.post("/search", response_class=HTMLResponse)
async def search(request: Request, question: str = Form(...)):
    """Gère la soumission du formulaire et affiche les résultats."""
    query_obj = Query(question=question)
    response = await query_endpoint(query_obj)
    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "question": question,
            "answer": response.answer,
            "citations": response.citations,
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)