#!/usr/bin/env python3
# kaitiaki/scripts/create_bm25_index.py
"""
Script rapide pour créer uniquement l'index BM25 manquant
"""

import sys
import json
import pickle
from pathlib import Path
from rank_bm25 import BM25Okapi

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

def create_bm25_index():
    """Crée l'index BM25 à partir des fichiers normalisés existants"""
    try:
        from kaitiaki.utils.settings import CFG
        
        processed_dir = Path(CFG["paths"]["data_processed"])
        bm25_index_path = Path(CFG["paths"]["bm25_index"])
        bm25_meta_path = Path(CFG["paths"]["bm25_meta"])
        
        print("🔍 Création de l'index BM25...")
        print(f"Source: {processed_dir}")
        print(f"Index: {bm25_index_path}")
        print(f"Meta: {bm25_meta_path}")
        
        # 1. Collecter tous les chunks
        chunks = []
        normalized_files = list(processed_dir.glob("*.normalized.json"))
        
        if not normalized_files:
            print("❌ Aucun fichier normalisé trouvé!")
            print("💡 Lancez d'abord: python -m kaitiaki.ingest.normalize")
            return False
        
        print(f"📚 Traitement de {len(normalized_files)} fichiers...")
        
        for f in normalized_files:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                for chunk in data.get("chunks", []):
                    chunks.append(chunk)
            except Exception as e:
                print(f"⚠️ Erreur lecture {f.name}: {e}")
                continue
        
        if not chunks:
            print("❌ Aucun chunk trouvé dans les fichiers!")
            return False
            
        print(f"📄 {len(chunks)} chunks collectés")
        
        # 2. Tokenisation pour BM25
        def tokenize(text: str) -> list:
            """Simple tokenization for French/English"""
            return [token for token in text.lower().split() if len(token) > 2]
        
        print("🔤 Tokenisation en cours...")
        texts = [chunk["text"] for chunk in chunks]
        tokenized_corpus = [tokenize(text) for text in texts]
        
        # 3. Créer l'index BM25
        print("🏗️ Construction de l'index BM25...")
        bm25 = BM25Okapi(tokenized_corpus)
        
        # 4. Préparer les métadonnées
        meta = []
        for chunk in chunks:
            meta.append({
                "doc_id": chunk.get("doc_id", "unknown"),
                "page": chunk.get("page", 0),
                "source": chunk.get("source", "AUTO"),
                "date": chunk.get("date", "unknown"),
                "parsing_method": chunk.get("parsing_method", "basic"),
                "semantic_context": chunk.get("semantic_context", "Standard content"),
            })
        
        # 5. Sauvegarder l'index
        print("💾 Sauvegarde de l'index...")
        
        # Créer le dossier si nécessaire
        bm25_index_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(bm25_index_path, "wb") as f:
            pickle.dump({
                "bm25": bm25,
                "tokenized": tokenized_corpus
            }, f)
        
        # 6. Sauvegarder les métadonnées
        bm25_meta_path.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        print("✅ Index BM25 créé avec succès!")
        print(f"   • Documents indexés: {len(meta)}")
        print(f"   • Fichier index: {bm25_index_path}")
        print(f"   • Fichier meta: {bm25_meta_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur création index BM25: {e}")
        return False

def test_bm25_index():
    """Test rapide de l'index BM25"""
    try:
        from kaitiaki.utils.settings import CFG
        
        bm25_path = Path(CFG["paths"]["bm25_index"])
        bm25_meta_path = Path(CFG["paths"]["bm25_meta"])
        
        if not bm25_path.exists():
            print("❌ Index BM25 toujours manquant")
            return False
            
        # Test de chargement
        with open(bm25_path, "rb") as f:
            data = pickle.load(f)
        
        meta = json.loads(bm25_meta_path.read_text(encoding="utf-8"))
        
        # Test de recherche
        bm25 = data["bm25"]
        test_query = "salaire BTP"
        tokens = [t for t in test_query.lower().split() if len(t) > 2]
        scores = bm25.get_scores(tokens)
        
        # Trouver les meilleurs résultats
        top_indices = scores.argsort()[-5:][::-1]
        top_scores = [scores[i] for i in top_indices if scores[i] > 0]
        
        print("✅ Test de l'index BM25 réussi")
        print(f"   • Requête test: '{test_query}'")
        print(f"   • Résultats avec score > 0: {len(top_scores)}")
        
        if top_scores:
            print(f"   • Meilleur score: {max(top_scores):.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test BM25: {e}")
        return False

def main():
    print("🔧 CRÉATION RAPIDE INDEX BM25")
    print("=" * 40)
    
    success = create_bm25_index()
    
    if success:
        print("\n🧪 Test de l'index...")
        test_success = test_bm25_index()
        
        if test_success:
            print("\n🎉 Index BM25 créé et testé avec succès!")
            print("\n📝 Prochaines étapes:")
            print("1. Redémarrez l'API server pour prendre en compte l'index")
            print("2. Testez une requête pour vérifier la recherche hybride")
            print("3. Lancez l'évaluation: python -m kaitiaki.eval.evaluate")
        else:
            print("\n⚠️ Index créé mais test échoué")
    else:
        print("\n❌ Échec de création de l'index")
        print("💡 Vérifiez que vous avez des fichiers .normalized.json")
        print("   dans kaitiaki/data/processed/")

if __name__ == "__main__":
    main()