# kaitiaki/api/server.py
from fastapi import FastAPI, Request, Body, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import yaml
import time

from kaitiaki.rag.pipeline import hybrid_search
from kaitiaki.rag.llm_client import generate_answer
from kaitiaki.rag.schemas import Query, Answer
from kaitiaki.utils.settings import CFG

app = FastAPI()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# CFG = yaml.safe_load((Path(__file__).resolve().parents[1] / "config" / "app.yaml").read_text(encoding="utf-8"))

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ingest")
def ingest():
    # Pour MVP: lancez parse -> normalize -> indexer avec des sous-process si nécessaire
    return {"status": "TODO (lancer parse/normalize/indexer en local)"}

@app.post("/query", response_model=Answer)
def query(q: Query = Body(...)):

    print(f"def query(q: Query = Body(...)):")
    
    ranked, rt = hybrid_search(q.text, rerank_top_k= min(q.top_k, CFG["retrieval"]["rerank_top_k"]))
    # Concaténer quelques contexts
    contexts = [d.content for d, _ in ranked[:8]]
    t0 = time.time()
    answer_text = generate_answer(q.text, contexts)
    gen_ms = int((time.time() - t0) * 1000)

    # Citations simples (top 3)
    cits = []
    for d,_ in ranked[:3]:
        cits.append({
            "doc_id": d.meta.get("doc_id"),
            "page": d.meta.get("page"),
            "snippet": (d.content[:240] + "…") if len(d.content) > 240 else d.content
        })

    # return Answer(answer=answer_text, citations=cits, latency_ms=rt + gen_ms)
    return Answer(answer=answer_text, citations=cits, latency_breakdown=latency_details)

# Pages simples
@app.post("/search", response_class=HTMLResponse)
def search_page(request: Request, text: str = Form(...)): # <--- Le changement est ici
# def search_page(request: Request, text: str = Body(..., embed=True)):

    print(f"def search_page(request: Request, text: str = Body(..., embed=True)):")

    ranked, rt = hybrid_search(text)
    contexts = [d.content for d,_ in ranked[:6]]
    answer = generate_answer(text, contexts)
    cits = [{"doc_id": d.meta.get("doc_id"), "page": d.meta.get("page")} for d,_ in ranked[:3]]
    return templates.TemplateResponse("result.html", {"request": request, "q": text, "answer": answer, "cits": cits})

