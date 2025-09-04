# kaitiaki/ingest/adapt_from_kaikite.py
from pathlib import Path
import json
import re
from datetime import datetime
from kaitiaki.utils.logging import logger
from kaitiaki.utils.settings import CFG
from collections import defaultdict

PROC_DIR = Path(CFG["paths"]["data_processed"])

def guess_date_from_filename(name: str) -> str:
    """
    Extrait une date (YYYY-MM-DD) du nom de fichier.
    """
    m = re.search(r"(20\d{2}[-_]?\d{2}[-_]?\d{2})", name)
    if not m:
        return None
    s = m.group(1).replace("_", "-")
    if len(s) == 8:  # Supporte le format YYYYMMDD
        s = f"{s[:4]}-{s[4:6]}-{s[6:]}"
    return s

def main():
    """
    Transforme les sorties JSON de kai_kite en chunks sémantiques "parent/enfant"
    et les sauvegarde au format JSONL, prêts pour l'indexeur.
    """
    # On cible les fichiers JSON bruts de kai-kite, en ignorant les formats déjà traités.
    kai_kite_outputs = [
        f for f in PROC_DIR.glob("*.json")
        if not f.name.endswith(('.pages.json', '.normalized.json', '.normalized.jsonl'))
    ]
    
    if not kai_kite_outputs:
        logger.warning("Aucun fichier de sortie de kai_kite (*.json) trouvé dans data/processed/. Le script n'a rien à faire.")
        return

    logger.info(f"Adaptation de {len(kai_kite_outputs)} document(s) avec la logique sémantique parent/enfant...")

    for f in kai_kite_outputs:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            kai_kite_chunks = data.get("chunks", [])
            doc_id = data.get("source_file", f.name)
            date = guess_date_from_filename(doc_id) or datetime.today().date().isoformat()

            # --- Étape 1 : Grouper les chunks atomiques par section sémantique ---
            sections = defaultdict(list)
            for chunk in kai_kite_chunks:
                section_id = chunk.get("meta", {}).get("section_id")
                if section_id:
                    sections[section_id].append(chunk)

            final_chunks_to_write = []
            for section_id, child_chunks in sections.items():
                if not child_chunks:
                    continue

                # Assurer un ordre logique en triant les enfants par page et position verticale.
                child_chunks.sort(key=lambda c: (c['meta']['page'], c['meta']['coordinates'][1]))

                # --- Étape 2 : Créer le chunk "parent" pour le contexte ---
                # Le parent agrège le contenu de tous ses enfants.
                parent_content = "\n\n".join([c['content'] for c in child_chunks])
                first_child_meta = child_chunks[0]['meta']
                parent_chunk = {
                    "chunk_id": section_id,  # L'ID de la section devient l'ID du chunk parent.
                    "parent_id": None,       # Les parents n'ont pas de parent.
                    "chunk_type": "parent",
                    "doc_id": doc_id,
                    "date": date,
                    "page": first_child_meta.get("page", 0),
                    "text": parent_content,   # Contenu complet pour le LLM.
                    "element_type": "Section",
                    "parent_title": first_child_meta.get("parent_title", ""),
                }
                final_chunks_to_write.append(parent_chunk)

                # --- Étape 3 : Créer les chunks "enfants" pour la recherche ---
                # Chaque enfant est un élément atomique lié à son parent.
                for child in child_chunks:
                    meta = child.get("meta", {})
                    child_chunk = {
                        "chunk_id": meta.get("chunk_id", ""),
                        "parent_id": section_id, # Lien sémantique vers le parent.
                        "chunk_type": "child",
                        "doc_id": doc_id,
                        "date": date,
                        "page": meta.get("page", 0),
                        "text": child.get("content", ""), # Contenu précis pour la recherche.
                        "element_type": meta.get("element_type", "Text"),
                        "parent_title": meta.get("parent_title", ""),
                        "coordinates": meta.get("coordinates", [])
                    }
                    final_chunks_to_write.append(child_chunk)

            if final_chunks_to_write:
                # Sauvegarde au format .jsonl pour une ingestion scalable.
                out_path = PROC_DIR / f"{Path(doc_id).stem}.normalized.jsonl"
                with out_path.open("w", encoding="utf-8") as out_file:
                    for s_chunk in final_chunks_to_write:
                        out_file.write(json.dumps(s_chunk, ensure_ascii=False) + "\n")
                logger.info(f"  -> Fichier normalisé créé : {out_path.name} ({len(final_chunks_to_write)} chunks au total)")
            else:
                logger.warning(f"  -> Aucun chunk sémantique n'a pu être généré pour {f.name}.")

        except json.JSONDecodeError:
            logger.error(f"  -> ERREUR: Impossible de décoder le JSON du fichier {f.name}")
        except Exception as e:
            logger.error(f"  -> ERREUR inattendue avec le fichier {f.name}: {e}", exc_info=True)

if __name__ == "__main__":
    main()

