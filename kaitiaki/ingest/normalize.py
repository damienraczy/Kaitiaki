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
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        chunks.append(text[start:end])
        start = end - overlap
        if start < 0: start = 0
    return chunks

def main():
    for f in sorted(PROC.glob("*.pages.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        doc_id = data["doc_id"]
        date = guess_date_from_filename(doc_id) or datetime.today().date().isoformat()

        chunks = []
        for p in data["pages"]:
            for c in chunk_text(p["text"] or ""):
                chunks.append({
                    "doc_id": doc_id,
                    "date": date,
                    "page": p["page"],
                    "text": c,
                    "source": "AUTO",  # JONC/IEOM/ISEE à ajuster selon le fichier
                })

        out = PROC / f"{Path(doc_id).stem}.normalized.json"
        out.write_text(json.dumps({"doc_id": doc_id, "date": date, "chunks": chunks}, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Normalized:", doc_id, f"({len(chunks)} chunks)")

if __name__ == "__main__":
    main()
