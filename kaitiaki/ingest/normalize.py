# kaitiaki/ingest/normalize.py
from pathlib import Path
import json
import re
from datetime import datetime

PROC = Path(__file__).resolve().parents[1] / "data" / "processed"

def guess_date_from_filename(name: str) -> str:
    m = re.search(r"(20\d{2}[-_]?\d{2}[-_]?\d{2})", name)
    if not m:
        return None
    s = m.group(1).replace("_","-")
    if len(s) == 8:  # yyyymmdd
        s = f"{s[:4]}-{s[4:6]}-{s[6:]}"
    return s

def chunk_text(text: str, size=1400, overlap=200):
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        chunks.append(text[start:end])
        # L'ancienne logique pouvait créer une boucle infinie si end - overlap < start.
        # Nouvelle logique pour avancer de manière sûre.
        start += (size - overlap)
    return chunks


# def chunk_text(text: str, size=1400, overlap=200):
#     text = re.sub(r"\s+", " ", text).strip()
#     chunks = []
#     start = 0
#     while start < len(text):
#         end = min(len(text), start + size)
#         chunks.append(text[start:end])
#         start = end - overlap
#         if start < 0: start = 0
#     return chunks

# def main():
#     print(f"Normalizing documents... {sorted(PROC.glob('*.pages.json'))}")
#     for f in sorted(PROC.glob("*.pages.json")):
#         print(f"Documents : <<<---{f}--->>>")

#         data = json.loads(f.read_text(encoding="utf-8"))
#         doc_id = data["doc_id"]
#         date = guess_date_from_filename(doc_id) or datetime.today().date().isoformat()
#         print(F"Document ID: {doc_id}, Date: {date}")

#         chunks = []
#         print(f"nb elements de data pages: {len(data['pages'])}")
#         for p in data["pages"]:
#             print(f"nb de chunk_text: {len(chunk_text(p['text'] or ''))}")
#             for c in chunk_text(p["text"] or ""):
#                 chunks.append({
#                     "doc_id": doc_id,
#                     "date": date,
#                     "page": p["page"],
#                     "text": c,
#                     "source": "AUTO",  # JONC/IEOM/ISEE à ajuster selon le fichier
#                 })

#         out = PROC / f"{Path(doc_id).stem}.normalized.json"
#         out.write_text(json.dumps({"doc_id": doc_id, "date": date, "chunks": chunks}, ensure_ascii=False, indent=2), encoding="utf-8")
#         print("Normalized:", doc_id, f"({len(chunks)} chunks)")

def main():
    files_to_process = sorted(PROC.glob("*.pages.json"))
    print(f"Normalizing {len(files_to_process)} documents...")

    for f in files_to_process:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            doc_id = data["doc_id"]
            date = guess_date_from_filename(doc_id) or datetime.today().date().isoformat()

            all_chunks = []
            for p in data["pages"]:
                page_text = p.get("text") or ""
                # Si le texte de la page est vide, on passe à la suivante
                if not page_text.strip():
                    continue

                for c in chunk_text(page_text):
                    all_chunks.append({
                        "doc_id": doc_id,
                        "date": date,
                        "page": p["page"],
                        "text": c,
                        "source": "AUTO",
                    })

            # N'écrire le fichier que s'il y a des chunks à sauvegarder
            if all_chunks:
                out_path = PROC / f"{Path(doc_id).stem}.normalized.json"
                out_data = {
                    "doc_id": doc_id,
                    "date": date,
                    "chunks": all_chunks
                }
                out_path.write_text(json.dumps(out_data, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"  -> Normalized: {doc_id} ({len(all_chunks)} chunks)")
            else:
                print(f"  -> Skipped (no text found): {doc_id}")

        except json.JSONDecodeError:
            print(f"  -> ERROR: Could not decode JSON from {f.name}")
        except Exception as e:
            print(f"  -> ERROR: An unexpected error occurred with {f.name}: {e}")

if __name__ == "__main__":
    main()
