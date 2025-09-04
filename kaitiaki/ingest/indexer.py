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
from kaitiaki.utils.logging import logger

PROC = Path(CFG["paths"]["data_processed"])

def yield_chunks():
    """
    Lit les fichiers .jsonl de manière robuste, en gérant les objets JSON
    qui s'étendent sur plusieurs lignes (ex: fichiers indentés).
    """
    for f in sorted(PROC.glob("*.normalized.jsonl")):
        logger.info(f"Lecture du fichier de chunks : {f.name}")
        try:
            with f.open("r", encoding="utf-8") as in_file:
                content = in_file.read()
                decoder = json.JSONDecoder()
                pos = 0
                
                while pos < len(content):
                    while pos < len(content) and content[pos].isspace():
                        pos += 1
                    if pos == len(content):
                        break

                    try:
                        obj, end_pos = decoder.raw_decode(content[pos:])
                        yield obj
                        pos += end_pos
                    except json.JSONDecodeError:
                        logger.error(f"Erreur de décodage JSON dans {f.name} à la position {pos}. Arrêt de la lecture pour ce fichier.")
                        break
        except Exception as e:
            logger.error(f"Impossible de lire ou traiter le fichier {f.name}: {e}")


def build_bm25_index(chunks):
    """
    Construit l'index BM25 en utilisant UNIQUEMENT les chunks "enfants"
    pour une recherche par mots-clés plus précise.
    """
    def tok(s): return [t for t in s.lower().split() if len(t) > 2]
    
    # Filtrer pour ne garder que les enfants
    child_chunks = [c for c in chunks if c.get("chunk_type") == "child"]
    logger.info(f"Construction de l'index BM25 sur {len(child_chunks)} chunks enfants.")

    if not child_chunks:
        return None, None, None

    texts = [c["text"] for c in child_chunks]
    tokenized = [tok(t) for t in texts]
    bm25 = BM25Okapi(tokenized)
    
    # La méta de BM25 doit contenir le chunk_id pour un mapping parfait
    meta = [
        {"chunk_id": c.get("chunk_id")} for c in child_chunks
    ]
    return bm25, tokenized, meta



def main():

    embedder = SentenceTransformer(CFG["embedding"]["model"])
    embedding_dim = embedder.get_sentence_embedding_dimension()

    store = QdrantDocumentStore(
        host=CFG["qdrant"]["host"],
        port=CFG["qdrant"]["port"],
        index=CFG["qdrant"]["index"],
        embedding_dim=embedding_dim,
        recreate_index=True,
    )

    client = QdrantClient(host=CFG["qdrant"]["host"], port=CFG["qdrant"]["port"])
    collection_name = CFG["qdrant"]["index"]
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config={"size": embedding_dim, "distance": "Cosine"}
    )
    logger.info(f"Index Qdrant recréé : {collection_name}")
    
    all_chunks = list(yield_chunks())

    if not all_chunks:
        logger.warning("Aucun chunk à indexer.")
        return
    
    logger.info(f"{len(all_chunks)} chunks (parents et enfants) trouvés pour l'indexation.")

    docs = []
    for ch in all_chunks:
        # On passe l'objet chunk entier dans les métadonnées
        # pour préserver toute l'information sémantique.
        d = Document(
            content=ch["text"],
            meta=ch
        )
        docs.append(d)

    logger.info(f'Calcul des embeddings pour {len(docs)} documents avec le modèle : {CFG["embedding"]["model"]}')
    embeddings = embedder.encode(
        [d.content for d in docs],
        batch_size=CFG.get("ingest", {}).get("batch_size", 64),
        normalize_embeddings=True,
        show_progress_bar=True
    )
    
    for doc, emb in zip(docs, embeddings):
        doc.embedding = emb.tolist()

    store.write_documents(docs)
    logger.info("Documents et embeddings écrits dans Qdrant.")

    # 4) BM25 local (pickle) sur les chunks enfants uniquement
    bm25, tokenized, meta = build_bm25_index(all_chunks)
    if bm25:
        with open(CFG["paths"]["bm25_index"], "wb") as w:
            pickle.dump({"bm25": bm25, "tokenized": tokenized}, w)
        Path(CFG["paths"]["bm25_meta"]).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Index BM25 local créé avec succès.")
    else:
        logger.warning("Aucun chunk enfant trouvé, l'index BM25 n'a pas été créé.")


if __name__ == "__main__":
    main()

