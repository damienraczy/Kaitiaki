# kaitiaki/rag/llm_client.py
import requests
from kaitiaki.utils.settings import CFG, settings
# import yaml
# from pathlib import Path

# CFG = yaml.safe_load((Path(__file__).resolve().parents[1] / "config" / "app.yaml").read_text(encoding="utf-8"))

def generate_answer(question: str, contexts: list[str]) -> str:
    """Appel à une API OpenAI-compatible locale (vLLM ou autre)."""
    # prompt = (
    #     "Vous êtes Kaitiaki, assistant de veille. "
    #     "Répondez en français de manière concise et sourcée. "
    #     "Citez les extraits pertinents en fin de réponse.\n\n"
    #     f"Question: {question}\n\n"
    #     "Contexte:\n" + "\n---\n".join(contexts[:8]) + "\n\n"
    #     "Réponse:"
    # )

    # --- NOUVEAU PROMPT HYBRIDE ---

    # joined_contexts = "\n---\n".join(contexts[:8])
    joined_contexts = "\n---\n".join(contexts)
    print(f"joined contexts = {joined_contexts}")
    prompt = f"""
**SYSTEM INSTRUCTIONS (Follow these rules strictly):**
1.  **You are Kaitiaki, an expert document analysis assistant for New Caledonia.**
2.  **Your task is to answer the user's question based *only* on the provided "Contexte".** Do not use any external knowledge.
3.  **If the answer is not in the "Contexte", you MUST reply with the exact sentence: "L'information n'est pas disponible dans les documents fournis."** Do not try to guess or infer an answer.
4.  **Your final answer MUST be in French.**

---
**Contexte :**
{joined_contexts}
---
**Question :**
{question}
---
**Réponse (in French):**
"""


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
