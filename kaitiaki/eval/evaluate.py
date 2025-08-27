# kaitiaki/eval/evaluate.py
import os, sys, json, time, statistics
from pathlib import Path
from typing import Dict, List, Tuple
import requests
import yaml

# Permet d'importer les modules du projet
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kaitiaki.rag.pipeline import hybrid_search
from kaitiaki.rag.schemas import Answer  # seulement pour le format
from kaitiaki.utils.settings import CFG

# CFG = yaml.safe_load((ROOT / "config" / "app.yaml").read_text(encoding="utf-8"))

API_URL = os.environ.get("KAI_API", "http://127.0.0.1:8000")
TESTSET_PATH = ROOT / "eval" / "qa_testset.json"
PAGES_DIR = ROOT / "data" / "processed"

def load_testset() -> List[Dict]:
    return json.loads(TESTSET_PATH.read_text(encoding="utf-8"))

def load_page_text(doc_id: str, page: int) -> str:
    """Charge le texte brut d'une page à partir de *.pages.json généré par parse_pdf.py"""
    pages_file = PAGES_DIR / f"{Path(doc_id).stem}.pages.json"
    if not pages_file.exists():
        return ""
    data = json.loads(pages_file.read_text(encoding="utf-8"))
    for p in data.get("pages", []):
        if int(p.get("page", -1)) == int(page):
            return (p.get("text") or "").strip()
    return ""

def call_api(question: str) -> Tuple[Dict, int]:
    """Appel end-to-end pour mesurer la latence globale ; retourne (json, wall_ms)"""
    t0 = time.time()
    r = requests.post(f"{API_URL}/query", json={"text": question})
    r.raise_for_status()
    wall_ms = int((time.time() - t0) * 1000)
    print(f"API call latency: {wall_ms} ms - status {r.status_code}")
    return r.json(), wall_ms

def topk_docpage_from_hybrid(question: str, k: int = 20) -> List[Tuple[str, int]]:
    """Utilise le retrieval pour estimer le recall@k (doc_id, page) après fusion + rerank."""
    ranked, _ = hybrid_search(question, rerank_top_k=k)
    ids = []
    for d, _score in ranked[:k]:
        doc_id = d.meta.get("doc_id")
        page = int(d.meta.get("page", -1))
        ids.append((doc_id, page))
    return ids

def citations_validity(resp: Dict, snippet_min_len: int = 40) -> float:
    """Vérifie que chaque citation est plausible:
       - presence d'une page dans le doc référencé
       - le snippet (si présent) existe réellement dans le texte de la page
    """
    cits = resp.get("citations", [])
    if not cits:
        return 0.0
    ok = 0
    for c in cits:
        doc_id = c.get("doc_id")
        page = c.get("page")
        snippet = (c.get("snippet") or "").strip()
        page_text = load_page_text(doc_id, page)
        cond_page = len(page_text) > 0
        cond_snip = (len(snippet) >= snippet_min_len and snippet in page_text) if snippet else True
        if cond_page and cond_snip:
            ok += 1
    return ok / len(cits)

def recall_at_k(gt: List[Dict], retrieved: List[Tuple[str,int]], k: int = 20) -> float:
    """gt: [{"doc_id":..., "page":...}, ...] ; retrieved: [(doc_id,page), ...]"""
    if not gt:
        return 1.0
    retrieved_k = set(retrieved[:k])
    hits = sum(1 for g in gt if (g["doc_id"], int(g.get("page", -1))) in retrieved_k)
    return hits / len(gt)

def run_eval():
    tests = load_testset()
    latencies = []         # p95 calculé sur latence end-to-end API
    recalls = []           # recall@20 basé sur retrieval
    cit_valid_rates = []   # taux de citations valides (0..1)
    per_item = []

    for i, t in enumerate(tests, start=1):
        q = t["question"]
        # gt = t.get("expected_citations", [])
        gt = t["expected_citations"]
        
        # 1) retrieval pour recall@20
        retrieved = topk_docpage_from_hybrid(q, k=20)
        r_at_20 = recall_at_k(gt, retrieved, k=20)
        recalls.append(r_at_20)

        # 2) appel API pour latence & citations
        try:
            resp, wall_ms = call_api(q)
        except Exception as e:
            per_item.append({
                "i": i, "question": q, "error": str(e), "recall@20": r_at_20
            })
            latencies.append(99999)
            cit_valid_rates.append(-1.0)
            continue

        latencies.append(wall_ms if "latency_ms" not in resp else resp["latency_ms"])
        cit_rate = citations_validity(resp)
        cit_valid_rates.append(cit_rate)

        per_item.append({
            "i": i,
            "question": q,
            "recall@20": round(r_at_20, 3),
            "citations_valid_rate": round(cit_rate, 3),
            "latency_ms": resp.get("latency_ms", wall_ms),
            "n_citations": len(resp.get("citations", []))
        })

    # Agrégats
    p95 = int(statistics.quantiles(latencies, n=100)[94]) if len(latencies) >= 2 else latencies[0]
    report = {
        "n": len(tests),
        "latency_p95_ms": p95,
        "latency_avg_ms": int(sum(latencies) / max(1, len(latencies))),
        "recall@20_avg": round(sum(recalls)/max(1,len(recalls)), 3),
        "cit_valid_rate_avg": round(sum(cit_valid_rates)/max(1,len(cit_valid_rates)), 3),
        "items": per_item
    }

    out_json = ROOT / "eval" / "report.json"
    out_csv  = ROOT / "eval" / "report.csv"

    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # CSV simple
    lines = ["i,question,recall_at_20,citations_valid_rate,latency_ms,n_citations"]
    for it in per_item:
        lines.append(f'{it.get("i")},{it.get("question").replace(",",";")},{it.get("recall@20",0)},{it.get("citations_valid_rate",0)},{it.get("latency_ms",0)},{it.get("n_citations",0)}')
    out_csv.write_text("\n".join(lines), encoding="utf-8")

    print("=== Résumé ===")
    print(json.dumps({k:v for k,v in report.items() if k != "items"}, ensure_ascii=False, indent=2))
    print(f"\nDétails enregistrés dans: {out_json}\nTableau: {out_csv}")

if __name__ == "__main__":
    run_eval()
