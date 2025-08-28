import time
import json
import csv
import requests
from tqdm import tqdm
import warnings

from kaitiaki.utils.logging import logger

# Configuration
API_URL = "http://127.0.0.1:8000/query"
QA_TESTSET_PATH = "kaitiaki/eval/qa_testset.json"
REPORT_JSON_PATH = "kaitiaki/eval/report.json"
REPORT_CSV_PATH = "kaitiaki/eval/report.csv"

def load_testset(filepath: str) -> list[dict]:
    """Charge le jeu de données de test depuis un fichier JSON."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Fichier de test non trouvé : {filepath}")
        return []

def run_evaluation(testset: list[dict]) -> list[dict]:
    """Exécute l'évaluation sur l'ensemble du jeu de données."""
    results = []
    for item in tqdm(testset, desc="Évaluation du pipeline RAG"):
        question = item["question"]
        expected_citations = {d["doc_id"] for d in item.get("expected_citations", [])}
        
        start_time = time.time()
        try:
            response = requests.post(API_URL, json={"question": question}, timeout=30)
            response.raise_for_status()
            api_response = response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur de l'API pour la question '{question}': {e}")
            continue
        finally:
            end_time = time.time()
            
        wall_ms = int((end_time - start_time) * 1000)

        # Extraction de la latence
        latency_info = api_response.get("latency")
        if latency_info and "totalMs" in latency_info:
            latency_ms = latency_info["totalMs"]
        else:
            warnings.warn(
                f"La réponse de l'API pour la question '{question}' ne contient pas de "
                f"champ de latence valide. Utilisation du temps 'wall time' ({wall_ms}ms) à la place."
            )
            latency_ms = wall_ms

        # Calcul des métriques
        retrieved_citations = {cite["documentId"] for cite in api_response.get("citations", [])}
        
        # Recall@20
        recall = len(expected_citations.intersection(retrieved_citations)) / len(expected_citations) if expected_citations else 0.0
        
        # Taux de citations valides
        citations_valid_rate = recall # Pour cet exemple, on simplifie

        results.append({
            "question": question,
            "answer": api_response.get("answer", ""),
            "latency_ms": latency_ms,
            "recall@20": recall,
            "citations_valid_rate": citations_valid_rate,
            "retrieved_citations": list(retrieved_citations),
            "expected_citations": list(expected_citations),
        })
        
    return results

def save_reports(results: list[dict]):
    """Sauvegarde les résultats de l'évaluation aux formats JSON et CSV."""
    if not results:
        logger.warning("Aucun résultat à sauvegarder.")
        return

    # Calcul des métriques agrégées
    avg_latency = sum(r["latency_ms"] for r in results) / len(results)
    avg_recall = sum(r["recall@20"] for r in results) / len(results)
    avg_valid_rate = sum(r["citations_valid_rate"] for r in results) / len(results)

    summary = {
        "num_questions": len(results),
        "avg_latency_ms": round(avg_latency, 2),
        "recall@20_avg": round(avg_recall, 4),
        "citations_valid_rate_avg": round(avg_valid_rate, 4),
    }

    report_data = {"summary": summary, "results": results}

    # Sauvegarde en JSON
    with open(REPORT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Rapport JSON sauvegardé dans {REPORT_JSON_PATH}")

    # Sauvegarde en CSV
    fieldnames = [
        "question", "answer", "latency_ms", "recall@20", 
        "citations_valid_rate", "retrieved_citations", "expected_citations"
    ]
    with open(REPORT_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for res in results:
            writer.writerow({k: res.get(k, "") for k in fieldnames})
    logger.info(f"Rapport CSV sauvegardé dans {REPORT_CSV_PATH}")

def main():
    """Fonction principale pour lancer l'évaluation."""
    logger.info("Démarrage de l'évaluation du pipeline RAG...")
    qa_testset = load_testset(QA_TESTSET_PATH)
    if not qa_testset:
        return
    
    evaluation_results = run_evaluation(qa_testset)
    save_reports(evaluation_results)
    logger.info("Évaluation terminée.")

if __name__ == "__main__":
    main()