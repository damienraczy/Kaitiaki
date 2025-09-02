Absolument. Voici la documentation pour `kaitiaki`, expliquant sa place et son fonctionnement au sein du processus global.

-----

### **Documentation : `kaitiaki` – Moteur de Recherche et de Génération (RAG)**

#### **Rôle dans le Processus Global**

`kaitiaki` constitue le **cœur applicatif** du système. Il intervient après `kai_kite` et a deux responsabilités principales :

1.  **Indexer :** Recevoir les données structurées extraites par `kai_kite`, les transformer en vecteurs numériques (embeddings), et les charger dans une base de données de recherche optimisée.
2.  **Répondre :** Exposer une API web qui accepte les questions des utilisateurs, orchestre un pipeline de recherche hybride pour trouver les informations les plus pertinentes, et utilise un Grand Modèle de Langage (LLM) pour générer une réponse synthétique et sourcée.

#### **Architecture et Modèles Utilisés**

`kaitiaki` implémente une architecture de **RAG (Retrieval-Augmented Generation) hybride** pour maximiser la pertinence des résultats en combinant deux approches de recherche.

Les modèles suivants sont utilisés :

1.  **Modèle d'Embeddings (`sentence-transformers/all-MiniLM-L6-v2`)** :

      * **Rôle :** Pendant l'indexation, il convertit les chunks de texte en vecteurs sémantiques. Lors d'une requête, il convertit également la question de l'utilisateur en vecteur pour permettre une recherche par similarité dans la base **Qdrant**.

2.  **Modèle de Reranking (`mixedbread-ai/mxbai-rerank-xsmall-v1`)** :

      * **Rôle :** Il intervient après la recherche pour ré-évaluer et classer les documents candidats. C'est une étape de raffinement cruciale qui améliore significativement la pertinence des extraits de contexte fournis au LLM.

3.  **Grand Modèle de Langage (LLM) (ex: `gpt-oss:20b`)** :

      * **Rôle :** C'est le composant final du pipeline. Il prend la question et les extraits les plus pertinents (fournis par le reranker) pour générer une réponse cohérente, rédigée en français, et accompagnée de citations.

#### **Flux de Données (Data Flow)**

Le processus `kaitiaki` se divise en deux flux distincts : l'indexation et la requête.

**Flux 1 : Indexation**

1.  **Entrée :** Le processus démarre avec les fichiers `*.normalized.json` créés par le script `adapt_from_kaikite.py` dans le dossier `kaitiaki/data/processed/`.
2.  **Calcul des Embeddings :** Le script `kaitiaki/ingest/indexer.py` lit chaque chunk de texte, et le **modèle d'Embeddings** le transforme en vecteur.
3.  **Création des Index :**
      * Les chunks et leurs vecteurs sont envoyés et stockés dans la base de données vectorielle **Qdrant**.
      * Parallèlement, un index de recherche par mots-clés (**BM25**) est construit à partir de l'ensemble des textes et sauvegardé dans le fichier `bm25_index.pkl`.
4.  **Sortie :** Une base de données Qdrant peuplée et un fichier d'index BM25, prêts pour la recherche.

**Flux 2 : Requête et Génération**

1.  **Entrée :** Un utilisateur soumet une question via l'interface web, déclenchant un appel à l'API `POST /query` de FastAPI.
2.  **Recherche Hybride (`search_engine.py`) :**
      * **Recherche Dense :** La question est vectorisée et utilisée pour trouver les chunks les plus similaires dans Qdrant.
      * **Recherche Lexicale :** La question est utilisée pour trouver les chunks les plus pertinents dans l'index BM25.
3.  **Fusion (`fusion.py`) :** Les deux listes de résultats sont combinées en une seule liste optimisée via l'algorithme RRF.
4.  **Reranking :** Le **modèle de Reranking** affine le classement de cette liste fusionnée.
5.  **Génération (`llm_client.py`) :** Les meilleurs chunks après reranking sont envoyés comme contexte au **LLM**, avec la question originale.
6.  **Sortie :** Le LLM génère la réponse finale. Le serveur FastAPI la formate en JSON avec les citations (source, page) et la renvoie au navigateur de l'utilisateur.

#### **Commandes d'Exécution**

Le processus `kaitiaki` est activé par les commandes suivantes, après l'exécution de `kai_kite` :

1.  **Normalisation des données (Adaptateur) :**

    ```bash
    python -m kaitiaki.ingest.adapt_from_kaikite
    ```

2.  **Indexation des données normalisées :**

    ```bash
    python -m kaitiaki.ingest.indexer
    ```

3.  **Lancement du serveur web :**

    ```bash
    uvicorn kaitiaki.api.server:app --reload
    ```