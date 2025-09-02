# kaitiaki/ingest/adapt_from_kaikite.py
from pathlib import Path
import json
import re
from datetime import datetime
from kaitiaki.utils.logging import logger
from kaitiaki.utils.settings import CFG

# Le dossier où kai_kite écrit ses sorties et où l'indexeur lira les siennes
PROC_DIR = Path(CFG["paths"]["data_processed"])

def guess_date_from_filename(name: str) -> str:
    """Extrait une date du nom de fichier (inchangé)."""
    m = re.search(r"(20\d{2}[-_]?\d{2}[-_]?\d{2})", name)
    if not m:
        return None
    s = m.group(1).replace("_", "-")
    if len(s) == 8:  # Format YYYYMMDD
        s = f"{s[:4]}-{s[4:6]}-{s[6:]}"
    return s

def main():
    """
    Lit les sorties JSON de kai_kite et les transforme en fichiers *.normalized.json
    pour l'indexeur de kaitiaki.
    """
    # On cherche les fichiers JSON qui ne sont PAS les fichiers intermédiaires
    kai_kite_outputs = [
        f for f in PROC_DIR.glob("*.json")
        if not f.name.endswith(('.pages.json', '.normalized.json'))
    ]
    
    if not kai_kite_outputs:
        logger.warning("Aucun fichier de sortie de kai_kite trouvé dans data/processed/. Avez-vous bien lancé le pipeline kai_kite avant ?")
        return

    logger.info(f"Adaptation de {len(kai_kite_outputs)} document(s) depuis la sortie de kai_kite...")

    for f in kai_kite_outputs:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            
            kai_kite_chunks = data.get("chunks", [])
            doc_id = data.get("source_file", f.name)
            date = guess_date_from_filename(doc_id) or datetime.today().date().isoformat()

            kaitiaki_chunks = []
            for chunk in kai_kite_chunks:
                # Mapping des champs : on transforme le format de kai_kite vers celui de kaitiaki
                kaitiaki_chunks.append({
                    "doc_id": doc_id,
                    "date": date,
                    "page": chunk["meta"].get("page", 0),
                    "text": chunk.get("content", ""),
                    "source": chunk["meta"].get("element_type", "AUTO"), # On enrichit la source
                })

            if kaitiaki_chunks:
                # On sauvegarde le fichier au format *.normalized.json
                out_path = PROC_DIR / f"{Path(doc_id).stem}.normalized.json"
                out_data = {
                    "doc_id": doc_id,
                    "date": date,
                    "chunks": kaitiaki_chunks
                }
                out_path.write_text(json.dumps(out_data, ensure_ascii=False, indent=2), encoding="utf-8")
                logger.info(f"  -> Fichier normalisé créé : {out_path.name} ({len(kaitiaki_chunks)} chunks)")
            else:
                logger.warning(f"  -> Aucun chunk trouvé dans {f.name}, fichier normalisé non créé.")

        except json.JSONDecodeError:
            logger.error(f"  -> ERREUR : Impossible de décoder le JSON du fichier {f.name}")
        except Exception as e:
            logger.error(f"  -> ERREUR inattendue avec le fichier {f.name}: {e}")

if __name__ == "__main__":
    main()