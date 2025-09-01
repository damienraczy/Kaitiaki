# kaitiaki/api/server.py
import time
from pathlib import Path
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from kaitiaki.rag.pipeline import hybrid_search
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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "timestamp": time.time(),
        "message": "Kaitiaki API is running"
    }

@app.post("/query", response_model=Answer)
async def query_endpoint(query: Query):
    """Traite une question et retourne une réponse structurée avec gestion d'erreurs robuste."""
    start_time = time.time()
    
    try:
        # Validation de base
        if not query.question or not query.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        logger.info(f"Processing query: {query.question[:100]}...")
        
        # Exécution du pipeline de recherche avec gestion d'erreurs
        try:
            ranked_results, retrieval_latency_ms = hybrid_search(query.question)
            logger.info(f"Search completed: {len(ranked_results)} results in {retrieval_latency_ms}ms")
        except Exception as e:
            logger.error(f"Search pipeline error: {e}")
            # Return a graceful error response instead of crashing
            error_latency = Latency(
                total_ms=int((time.time() - start_time) * 1000),
                retrieval_ms=0,
                llm_ms=0
            )
            return Answer(
                answer=f"Désolé, une erreur s'est produite lors de la recherche: {str(e)}. Vérifiez que l'indexation a bien été effectuée.",
                citations=[],
                latency=error_latency
            )
        
        # Préparation du contexte pour le LLM
        contexts = [doc.content for doc, score in ranked_results[:8]]
        
        if not contexts:
            logger.warning("No search results found, generating answer without context")
            contexts = ["Aucun document pertinent trouvé dans la base de connaissances."]
        
        # Génération de la réponse LLM avec gestion d'erreurs
        llm_start = time.time()
        try:
            generated_answer = generate_answer(query.question, contexts)
            logger.info("Answer generated successfully")
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            generated_answer = f"Désolé, je ne peux pas générer de réponse pour le moment. Erreur: {str(e)}. Vérifiez la configuration du LLM (Ollama)."
        
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
        citations = []
        try:
            for doc, score in ranked_results[:5]:
                citation = Citation(
                    document_id=doc.meta.get("doc_id", "ID inconnu"),
                    content=doc.content,
                    page_number=doc.meta.get("page", 0),
                    source=doc.meta.get("source", "Source inconnue")
                )
                citations.append(citation)
        except Exception as e:
            logger.warning(f"Error formatting citations: {e}")
            # Continue without citations rather than failing
        
        response = Answer(
            answer=generated_answer,
            citations=citations,
            latency=latency_details
        )
        
        logger.info(f"Query processed successfully in {total_latency_ms}ms")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error in query_endpoint: {e}")
        error_latency_ms = int((time.time() - start_time) * 1000)
        
        return Answer(
            answer=f"Une erreur inattendue s'est produite: {str(e)}. Consultez les logs pour plus de détails.",
            citations=[],
            latency=Latency(
                total_ms=error_latency_ms,
                retrieval_ms=0,
                llm_ms=0
            )
        )

@app.post("/search", response_class=HTMLResponse)
async def search(request: Request, question: str = Form(...)):
    """(Endpoint déprécié, utilisé par l'ancien formulaire) Gère la soumission du formulaire et affiche les résultats."""
    try:
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
    except Exception as e:
        logger.error(f"Error in search endpoint: {e}")
        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "q": question,
                "answer": f"Erreur: {str(e)}",
                "cits": [],
            },
        )

# Error handlers
@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}")
    return {"error": "Internal server error", "detail": str(exc)}

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    return {"error": "Not found", "detail": "The requested resource was not found"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Kaitiaki API server...")
    uvicorn.run(app, host="127.0.0.1", port=8000)