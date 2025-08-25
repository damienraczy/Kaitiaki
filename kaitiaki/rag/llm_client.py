# kaitiaki/rag/llm_client.py
import requests
import yaml
from pathlib import Path

CFG = yaml.safe_load((Path(__file__).resolve().parents[1] / "config" / "app.yaml").read_text(encoding="utf-8"))

def generate_answer(question: str, contexts: list[str]) -> str:
    """Appel à une API OpenAI-compatible locale (vLLM ou autre)."""
    prompt = (
        "Vous êtes Kaitiaki, assistant de veille. "
        "Répondez en français de manière concise et sourcée. "
        "Citez les extraits pertinents en fin de réponse.\n\n"
        f"Question: {question}\n\n"
        "Contexte:\n" + "\n---\n".join(contexts[:8]) + "\n\n"
        "Réponse:"
    )

    body = {
        "model": CFG["models"]["llm_model"],
        "messages": [{"role":"user","content": prompt}],
        "temperature": 0.2,
        "max_tokens": 600,
    }
    r = requests.post(f'{CFG["models"]["llm_base_url"].rstrip("/")}/chat/completions', json=body, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()
