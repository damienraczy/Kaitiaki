# kaitiaki/ingest/indexer.py
from pathlib import Path
import json
import pickle
from collections import defaultdict

import yaml
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from haystack import Document
from qdrant_client import QdrantClient
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from kaitiaki.utils.settings import CFG

# CFG = yaml.safe_load((Path(__file__).resolve().parents[1] / "config" / "app.yaml").read_text(encoding="utf-8"))
# PROC = Path(__file__).resolve().parents[1] / "data" / "processed"
PROC = Path(CFG["paths"]["data_processed"])

def yield_chunks():
    for f in sorted(PROC.glob("*.normalized.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        for ch in data["chunks"]:
            yield ch

def build_bm25_index(chunks):
    # Corpus tokenization simple (FR/EN)
    def tok(s): return [t for t in s.lower().split() if len(t) > 2]
    texts = [c["text"] for c in chunks]
    tokenized = [tok(t) for t in texts]
    bm25 = BM25Okapi(tokenized)
    meta = [{"doc_id": c["doc_id"], "page": c["page"]} for c in chunks]
    return bm25, tokenized, meta



def main():

    embedder = SentenceTransformer(CFG["embedding"]["model"])
    embedding_dim = embedder.get_sentence_embedding_dimension()

    # 1) Qdrant DocumentStore
    store = QdrantDocumentStore(
        host=CFG["qdrant"]["host"],
        port=CFG["qdrant"]["port"],
        index=CFG["qdrant"]["index"],      # specify index
        embedding_dim=embedding_dim,            # size of an embedding
        recreate_index=True,                    # optional: clears & recreates index
    )

    # 1.2) Nettoyage de l'index avant de commencer
    client = QdrantClient(
        host=CFG["qdrant"]["host"],
        port=CFG["qdrant"]["port"]
    )

    collection_name = CFG["qdrant"]["index"]
    client.delete_collection(collection_name=collection_name)

    print(f"Suppression de l'index Qdrant: {collection_name}")
    
    # 2) Charger et écrire les documents (chunks)
    docs = []
    for ch in yield_chunks():
        d = Document(
            content=ch["text"],
            meta={"doc_id": ch["doc_id"], "page": ch["page"], "date": ch["date"], "source": ch.get("source","AUTO")}
        )
        docs.append(d)

    if not docs:
        print("Aucun document à indexer. Vérifiez data/processed.")
        return

    # 3) Embeddings (dense)
    print(f'Calcul des embeddings...CFG["embedding"]["model"] = {CFG["embedding"]["model"]}')
    embeddings = embedder.encode(
        [d.content for d in docs],
        batch_size=64,
        normalize_embeddings=True,
        show_progress_bar=True
    )
    # Sauvegarde des embeddings dans le store
    for doc, emb in zip(docs, embeddings):
        doc.embedding = emb.tolist()
    # store.update_embeddings(docs)
    store.write_documents(docs)
    print("Embeddings mis à jour.")

    # 4) BM25 local (pickle)
    bm25, tokenized, meta = build_bm25_index([{"text": d.content, **d.meta} for d in docs])
    with open(CFG["paths"]["bm25_index"], "wb") as w:
        pickle.dump({"bm25": bm25, "tokenized": tokenized}, w)
    Path(CFG["paths"]["bm25_meta"]).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Index BM25 local créé.")

if __name__ == "__main__":
    main()
