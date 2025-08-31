# kaitiaki/rag/llm_client.py
import requests
from kaitiaki.utils.settings import CFG, settings
# import yaml
# from pathlib import Path

# CFG = yaml.safe_load((Path(__file__).resolve().parents[1] / "config" / "app.yaml").read_text(encoding="utf-8"))

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

    # body = {
    #     "model": CFG["llm"]["model"],
    #     "messages": [{"role":"user","content": prompt}],
    #     # "temperature": CFG["llm"]["temperature"],
    #     # "max_tokens": CFG["llm"]["max_tokens"],
    #     "stream": False # On demande une réponse complète, pas un flux
    # }

    body = {
        "model": CFG["llm"]["model"],
        "prompt": prompt,  # Pas "messages" !
        "stream": False,
        "options": {
            "temperature": CFG["llm"]["temperature"],
            "num_predict": CFG["llm"]["max_tokens"],
        }
    }

    endpoint = f'{CFG["llm"]["base_url"].rstrip("/")}/api/generate'

    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",        
        "Content-Type": "application/json"
    }
    

    # url = CFG["llm"]["llm_base_url"].rstrip("/") + "/chat/completions"
    endpoint = f'{CFG["llm"]["base_url"].rstrip("/")}' + "/generate"
    
    r = requests.post(
        endpoint,
        json=body,
        headers=headers,
        timeout=120
    )

    r.raise_for_status()
    r_json = r.json()
    response = r_json.get("response", "").strip()
    return response

    # return r.json()["choices"][0]["message"]["content"].strip()
