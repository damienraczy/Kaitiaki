#!/usr/bin/env python3
# kaitiaki/scripts/repair.py
"""
Script de réparation rapide pour Kaitiaki
Diagnostique et corrige les problèmes courants
"""

import sys
import json
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

def check_and_fix_data_pipeline():
    """Vérifier et corriger le pipeline de données"""
    print("🔧 VÉRIFICATION DU PIPELINE DE DONNÉES")
    print("="*50)
    
    try:
        from kaitiaki.utils.settings import CFG
        
        raw_dir = Path(CFG["paths"]["data_raw"])
        processed_dir = Path(CFG["paths"]["data_processed"]) 
        bm25_index = Path(CFG["paths"]["bm25_index"])
        bm25_meta = Path(CFG["paths"]["bm25_meta"])
        
        # 1. Check raw PDFs
        pdf_files = list(raw_dir.glob("*.pdf")) if raw_dir.exists() else []
        print(f"📄 PDFs trouvés: {len(pdf_files)}")
        
        if not pdf_files:
            print("❌ Aucun PDF trouvé dans kaitiaki/data/raw/")
            print("💡 Ajoutez vos PDFs dans ce dossier avant de continuer")
            return False
        
        # 2. Check processed files
        pages_files = list(processed_dir.glob("*.pages.json")) if processed_dir.exists() else []
        normalized_files = list(processed_dir.glob("*.normalized.json")) if processed_dir.exists() else []
        
        print(f"📑 Fichiers .pages.json: {len(pages_files)}")
        print(f"📚 Fichiers .normalized.json: {len(normalized_files)}")
        
        # 3. Check indexes
        print(f"🔍 Index BM25: {'✅' if bm25_index.exists() else '❌'}")
        print(f"📋 Métadonnées BM25: {'✅' if bm25_meta.exists() else '❌'}")
        
        # Determine what needs to be done
        need_parsing = len(pages_files) < len(pdf_files)
        need_normalization = len(normalized_files) < len(pages_files) 
        need_indexing = not (bm25_index.exists() and bm25_meta.exists())
        
        if need_parsing:
            print("\n🚨 PROBLÈME: Parsing incomplet")
            print("💡 Solution: python -m kaitiaki.ingest.parse_pdf")
            
        if need_normalization:
            print("\n🚨 PROBLÈME: Normalisation incomplète") 
            print("💡 Solution: python -m kaitiaki.ingest.normalize")
            
        if need_indexing:
            print("\n🚨 PROBLÈME: Indexation manquante")
            print("💡 Solution: python -m kaitiaki.ingest.indexer")
        
        if need_parsing or need_normalization or need_indexing:
            print("\n🎯 SOLUTION RAPIDE: Lancez le pipeline complet")
            print("   python -m kaitiaki.scripts.process_all")
            return False
        else:
            print("\n✅ Pipeline de données OK")
            return True
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def check_and_fix_qdrant():
    """Vérifier Qdrant"""
    print("\n🗃️ VÉRIFICATION QDRANT")
    print("="*50)
    
    try:
        from kaitiaki.utils.settings import CFG
        from qdrant_client import QdrantClient
        
        client = QdrantClient(
            host=CFG["qdrant"]["host"],
            port=CFG["qdrant"]["port"]
        )
        
        # Test connection
        collections = client.get_collections()
        print("✅ Qdrant accessible")
        
        collection_name = CFG["qdrant"]["index"]
        collection_names = [c.name for c in collections.collections]
        
        if collection_name not in collection_names:
            print(f"❌ Collection '{collection_name}' manquante")
            print("💡 Solution: Relancez l'indexation")
            print("   python -m kaitiaki.ingest.indexer")
            return False
        else:
            info = client.get_collection(collection_name)
            print(f"✅ Collection '{collection_name}' OK ({info.points_count} documents)")
            return True
            
    except Exception as e:
        print(f"❌ Qdrant inaccessible: {e}")
        print("💡 Solutions:")
        print("   1. Démarrez Qdrant: docker run -p 6333:6333 qdrant/qdrant")
        print("   2. Ou vérifiez la config dans kaitiaki/config/app.yaml")
        return False

def check_api_server():
    """Vérifier l'API server"""
    print("\n🌐 VÉRIFICATION API")
    print("="*50)
    
    try:
        response = requests.get("http://127.0.0.1:8000/", timeout=3)
        if response.status_code == 200:
            print("✅ API server accessible")
            return True
        else:
            print(f"⚠️ API répond avec code {response.status_code}")
            return False
    except requests.ConnectionError:
        print("❌ API server non accessible")
        print("💡 Solution: Démarrez l'API server")
        print("   python -m kaitiaki.api.server")
        return False
    except Exception as e:
        print(f"❌ Erreur API: {e}")
        return False

def test_basic_query():
    """Tester une requête basique"""
    print("\n🧪 TEST REQUÊTE BASIQUE")
    print("="*50)
    
    try:
        test_query = {"question": "test diagnostic"}
        response = requests.post(
            "http://127.0.0.1:8000/query", 
            json=test_query, 
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("answer", "")
            citations = result.get("citations", [])
            
            print(f"✅ Requête réussie")
            print(f"   • Réponse: {len(answer)} caractères")
            print(f"   • Citations: {len(citations)}")
            
            if len(answer) < 10:
                print("⚠️ Réponse très courte, vérifiez le LLM")
            
            if len(citations) == 0:
                print("⚠️ Aucune citation, vérifiez l'indexation")
            
            return True
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur requête: {e}")
        return False

def auto_repair():
    """Tentative de réparation automatique"""
    print("\n🔧 TENTATIVE DE RÉPARATION AUTOMATIQUE")
    print("="*50)
    
    try:
        # Check if we can auto-fix the most common issue: missing indexes
        from kaitiaki.utils.settings import CFG
        
        processed_dir = Path(CFG["paths"]["data_processed"])
        normalized_files = list(processed_dir.glob("*.normalized.json")) if processed_dir.exists() else []
        bm25_index = Path(CFG["paths"]["bm25_index"])
        
        if normalized_files and not bm25_index.exists():
            print("🔄 Tentative de création des index manquants...")
            import subprocess
            result = subprocess.run([
                sys.executable, "-m", "kaitiaki.ingest.indexer"
            ], capture_output=True, text=True, cwd=project_root)
            
            if result.returncode == 0:
                print("✅ Indexation réussie!")
                return True
            else:
                print(f"❌ Échec indexation: {result.stderr}")
                return False
        else:
            print("ℹ️ Aucune réparation automatique possible")
            return False
            
    except Exception as e:
        print(f"❌ Erreur réparation: {e}")
        return False

def main():
    """Script de réparation principal"""
    print("🚑 KAITIAKI - RÉPARATION RAPIDE")
    print("=" * 60)
    
    # Run diagnostics
    data_ok = check_and_fix_data_pipeline()
    qdrant_ok = check_and_fix_qdrant() 
    api_ok = check_api_server()
    
    if not api_ok:
        print("\n⚠️ API server non accessible - impossible de tester les requêtes")
        print("Lancez d'abord: python -m kaitiaki.api.server")
    else:
        query_ok = test_basic_query()
        
        if not query_ok and not data_ok:
            print("\n🔧 Tentative de réparation...")
            if auto_repair():
                print("✅ Réparation réussie! Redémarrez l'API server.")
            else:
                print("❌ Réparation échouée.")
    
    # Summary and recommendations
    print(f"\n📋 RÉSUMÉ")
    print("="*30)
    
    issues = []
    if not data_ok:
        issues.append("Pipeline de données")
    if not qdrant_ok:
        issues.append("Qdrant") 
    if not api_ok:
        issues.append("API server")
    
    if not issues:
        print("🎉 Système fonctionnel!")
    else:
        print(f"⚠️ Problèmes détectés: {', '.join(issues)}")
        print(f"\n📝 ACTIONS RECOMMANDÉES:")
        print("1. Suivez les solutions proposées ci-dessus")
        print("2. Ou lancez le pipeline complet: python -m kaitiaki.scripts.process_all")
        print("3. Puis redémarrez l'API: python -m kaitiaki.api.server")
    
    return len(issues) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)