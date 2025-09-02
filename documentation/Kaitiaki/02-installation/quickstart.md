# Démarrage rapide

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Déposer 6–10 PDF dans kaitiaki/data/raw/
python -m kaitiaki.ingest.parse_pdf
python -m kaitiaki.ingest.normalize
python -m kaitiaki.ingest.indexer

uvicorn kaitiaki.api.server:app --reload
# Ouvrir http://127.0.0.1:8000
````

Pour l’évaluation :

```bash
python -m kaitiaki.eval.evaluate
```

