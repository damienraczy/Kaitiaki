### **Vue d'ensemble de l'architecture**

L'architecture est composée de deux projets principaux qui fonctionnent en tandem : **`kai_kite`** pour l'ingestion intelligente des documents, et **`kaitiaki`** pour la recherche et la génération de réponses. L'ensemble forme un pipeline de **RAG (Retrieval-Augmented Generation) hybride**, conçu pour fonctionner localement ("on-premise") afin de garantir la souveraineté des données.

Les technologies principales sont :
* **Backend et API :** Python 3.11 avec FastAPI.
* **Orchestration RAG :** Haystack 2.x.
* **Stockage Vectoriel :** Qdrant, pour stocker les "embeddings" (vecteurs) des chunks de texte.
* **Recherche Lexicale :** Un index BM25 local, stocké dans un fichier `.pkl`, pour la recherche par mots-clés.

### **Les modèles et leur rôle**

Plusieurs modèles d'intelligence artificielle sont utilisés à différentes étapes du processus :

1.  **Modèle de détection de mise en page (Layout Detector)**
    * **Modèle :** YOLOv10 (par exemple, `yolov10s_best.pt`).
    * **Rôle :** Utilisé par `kai_kite`, ce modèle analyse l'image d'une page de document pour identifier visuellement les zones de contenu : titres, paragraphes, tableaux, listes, en-têtes et pieds de page. C'est la première étape de l'extraction intelligente.

2.  **Modèle de reconnaissance de tableaux (Table Transformer)**
    * **Modèle :** `microsoft/table-transformer-structure-recognition`.
    * **Rôle :** Également dans `kai_kite`, ce modèle est spécialisé dans l'analyse des images de tableaux. Il détecte la structure interne (cellules, lignes, colonnes) pour permettre une extraction fiable du contenu tabulaire.

3.  **Modèle d'Embeddings (Dense Retriever)**
    * **Modèle :** `sentence-transformers/all-MiniLM-L6-v2`.
    * **Rôle :** Utilisé par `kaitiaki`, ce modèle transforme les chunks de texte en vecteurs numériques (embeddings). Ces vecteurs capturent le sens sémantique du texte, permettant une recherche par similarité (trouver des passages qui parlent de la même chose, même avec des mots différents).

4.  **Modèle de Reranking (Cross-Encoder)**
    * **Modèle :** `mixedbread-ai/mxbai-rerank-xsmall-v1`.
    * **Rôle :** C'est un modèle crucial pour la pertinence. Après la première passe de recherche (hybride), il ré-évalue les documents candidats par rapport à la question posée et les réordonne pour placer les plus pertinents en tête.

5.  **Grand Modèle de Langage (LLM)**
    * **Modèle :** Un modèle local servi via une API compatible OpenAI (ex: `gpt-oss:20b` via Ollama).
    * **Rôle :** C'est le cerveau final du système. Il prend la question de l'utilisateur et les extraits de texte les plus pertinents fournis par le reranker, et génère une réponse synthétique et rédigée en français.

### **Flux de données de bout en bout**

Voici le parcours d'un document, du fichier PDF brut à la réponse affichée dans l'interface web.

#### **Phase 1 : Ingestion et Indexation (Pipeline `kai_kite` → `kaitiaki`)**

1.  **Entrée :** Des fichiers PDF sont placés dans le dossier `kaitiaki/data/raw/`.
2.  **Traitement par `kai_kite` :**
    * Les PDF sont convertis en images, page par page.
    * Le modèle **YOLO** analyse chaque image pour détecter les zones de contenu.
    * Pour chaque zone, le texte est extrait via OCR. Si une zone est un tableau, le **Table Transformer** est utilisé pour extraire les données de manière structurée.
    * **Sortie :** `kai_kite` génère un fichier JSON structuré par document dans `kaitiaki/data/processed/`, contenant des "chunks" sémantiques.

3.  **Adaptation et Normalisation :**
    * Le script `kaitiaki/ingest/adapt_from_kaikite.py` lit ces JSON.
    * **Sortie :** Il les transforme en fichiers `*.normalized.json`, le format attendu par l'indexeur de `kaitiaki`.

4.  **Indexation par `kaitiaki` :**
    * Le script `kaitiaki/ingest/indexer.py` lit les `*.normalized.json`.
    * Le **modèle d'Embeddings** convertit chaque chunk en vecteur.
    * **Sortie :** Les chunks et leurs vecteurs sont stockés dans la base de données **Qdrant**. En parallèle, un index de recherche par mots-clés (**BM25**) est créé et sauvegardé dans le fichier `bm25_index.pkl`.

#### **Phase 2 : Recherche et Génération (Pipeline RAG de `kaitiaki`)**

1.  **Entrée :** Un utilisateur pose une question dans l'interface web.
2.  **Recherche Hybride (Retrieval) :**
    * La requête est envoyée simultanément à deux moteurs de recherche :
        * **Recherche Dense :** Le **modèle d'Embeddings** vectorise la question et cherche les chunks sémantiquement similaires dans **Qdrant**.
        * **Recherche Lexicale :** La question est utilisée pour trouver les chunks contenant les mêmes mots-clés grâce à l'index **BM25**.
3.  **Fusion :**
    * Les résultats des deux recherches sont fusionnés en une seule liste grâce à l'algorithme **Reciprocal Rank Fusion (RRF)**, qui combine les classements des deux moteurs.

4.  **Ré-ordonnancement (Reranking) :**
    * Le **modèle de Reranking** prend la liste fusionnée et la réordonne finement pour obtenir les `top-k` résultats les plus pertinents.

5.  **Génération :**
    * Le **LLM** reçoit la question de l'utilisateur et le contenu des chunks les mieux classés.
    * **Sortie :** Il génère une réponse textuelle synthétique.

6.  **Restitution :**
    * Le serveur **FastAPI** renvoie la réponse générée ainsi que les métadonnées des chunks utilisés (source, page) qui sont affichées comme citations dans l'interface utilisateur.
    