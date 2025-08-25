# kaitiaki/ingest/parse_pdf.py
from pathlib import Path
import pdfplumber
import json
import os

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
PROC = Path(__file__).resolve().parents[1] / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

def extract_text(pdf_path: Path):
    pages = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append({"page": i, "text": text})
    return pages

def main():
    for f in sorted(RAW.glob("*.pdf")):
        out = PROC / f"{f.stem}.pages.json"
        if out.exists():
            continue
        pages = extract_text(f)
        with open(out, "w", encoding="utf-8") as w:
            json.dump({"doc_id": f.name, "pages": pages}, w, ensure_ascii=False, indent=2)
        print("Parsed:", f.name)

if __name__ == "__main__":
    main()
