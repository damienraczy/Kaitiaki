def test_qdrant_connection():
    """Script de validation de la configuration Qdrant"""
    from kaitiaki.utils.settings import CFG
    from qdrant_client import QdrantClient
    from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
    
    print("=== Test Configuration Qdrant ===")
    print(f"Host: {CFG['qdrant']['host']}")
    print(f"Port: {CFG['qdrant']['port']}")
    print(f"Index: {CFG['qdrant']['index']}")
    
    try:
        # Test 1: Connexion client direct
        client = QdrantClient(
            host=CFG["qdrant"]["host"],
            port=CFG["qdrant"]["port"]
        )
        print("✅ Connexion client Qdrant OK")
        
        # Test 2: Liste des collections
        collections = client.get_collections()
        print(f"📋 Collections: {[c.name for c in collections.collections]}")
        
        # Test 3: DocumentStore Haystack
        store = QdrantDocumentStore(
            host=CFG["qdrant"]["host"],
            port=CFG["qdrant"]["port"],
            index=CFG["qdrant"]["index"],
            embedding_dim=384,  # Dimension pour all-MiniLM-L6-v2
        )
        print("✅ DocumentStore Haystack OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur Qdrant: {e}")
        return False

if __name__ == "__main__":
    test_qdrant_connection()