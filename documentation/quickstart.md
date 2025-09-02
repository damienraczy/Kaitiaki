### **Guide de Démarrage Complet de Kaitiaki**

Ce guide décrit les étapes pour installer, ingérer les données et lancer l'application.

#### **1. Prérequis (Services Externes)**

Avant de lancer le code, assurez-vous que les services suivants sont démarrés et accessibles :

  * **Qdrant :** Lancez le binaire Qdrant. Par défaut, il doit être accessible sur `http://127.0.0.1:6333`.
    ```bash
    # Exemple de commande pour lancer Qdrant
    ./qdrant
    ```
  * **Serveur LLM :** Démarrez votre serveur de modèle de langage (ex: Ollama, vLLM). Il doit exposer une API compatible OpenAI.

#### **2. Installation**

Ces commandes préparent votre environnement de travail.

1.  **Créez et activez un environnement virtuel Python :**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
2.  **Installez les dépendances requises :**
    ```bash
    pip install -r requirements.txt
    ```

#### **3. Pipeline d'Ingestion des Données**

Ce processus en quatre étapes transforme vos PDF bruts en un index de recherche.

1.  **Ajoutez vos documents :**

      * Placez tous les fichiers PDF à traiter dans le dossier `kaitiaki/data/raw/`.

2.  **(Kai-kite) Lancez le parsing sémantique :**

      * Cette commande utilise `kai_kite` pour analyser la mise en page et extraire le contenu de manière structurée.

    <!-- end list -->

    ```bash
    python -m kai_kite.main kaitiaki/data/raw/
    ```

3.  **(Adaptateur) Normalisez les sorties de `kai_kite` :**

      * Cette commande transforme les fichiers JSON de `kai_kite` au format `*.normalized.json` attendu par l'indexeur.

    <!-- end list -->

    ```bash
    python -m kaitiaki.ingest.adapt_from_kaikite
    ```

4.  **(Kaitiaki) Lancez l'indexation :**

      * Cette commande finale lit les fichiers normalisés, calcule les embeddings, les charge dans Qdrant et crée l'index de recherche lexicale `bm25_index.pkl`.

    <!-- end list -->

    ```bash
    python -m kaitiaki.ingest.indexer
    ```

#### **4. Lancement de l'Application**

1.  **Démarrez le serveur web FastAPI :**
    ```bash
    uvicorn kaitiaki.api.server:app --reload
    ```
    *Le serveur va charger les modèles en mémoire et démarrer. Il est maintenant prêt à recevoir des requêtes.*

#### **5. Utilisation**

1.  **Ouvrez l'interface web :**
      * Dans votre navigateur, allez à l'adresse [http://127.0.0.1:8000](http://127.0.0.1:8000).
2.  **Posez votre question :**
      * Utilisez le champ de recherche pour interroger vos documents.

