# Kaitiaki — Assistant de Veille Stratégique pour la Nouvelle-Calédonie

**Kaitiaki** est un système de RAG (Retrieval-Augmented Generation) conçu pour interroger et synthétiser des corpus de documents publics (JONC, ISEE, IEOM, délibérations) concernant la Nouvelle-Calédonie.

Il fournit des réponses sourcées en langage naturel, avec des citations précises, pour aider les entreprises, consultants et institutions dans leur travail de veille.

## Architecture et Souveraineté des Données

Le projet est conçu selon une logique de **développement local** dans le but de fournir une solution garantissant une **souveraineté totale sur les données et l'infrastructure**. L'ensemble du pipeline est destiné à être déployé "on-premise", sans dépendance à des services cloud externes pour le traitement des informations sensibles.

L'architecture est divisée en deux composants principaux :

1.  **`kai_kite`** : Un pipeline d'ingestion intelligent qui utilise des modèles de vision par ordinateur (YOLOv10, Table Transformer) et l'OCR pour extraire le contenu des documents de manière sémantiquement structurée.
2.  **`kaitiaki`** : Le cœur de l'application, qui expose une API FastAPI et orchestre un pipeline RAG hybride (Recherche Dense + Lexicale + Reranking) pour répondre aux questions.

La recherche est basée sur **Qdrant** (vecteurs), un index **BM25** local (mots-clés) et un **LLM** pour la génération de réponses.

## Prérequis

Avant de commencer, assurez-vous que les services suivants sont installés et en cours d'exécution :

  * **Python 3.11+**
  * **Qdrant :** Un serveur Qdrant doit être accessible localement (par défaut `127.0.0.1:6333`).
  * **Serveur LLM :** Pour la version de production, un modèle de langage doit être servi localement via une API compatible OpenAI. (Voir la note ci-dessous pour le développement).

## Installation

1.  **Clonez le dépôt et créez un environnement virtuel :**

    ```bash
    git clone https://github.com/votre-utilisateur/Kaitiaki.git
    cd Kaitiaki
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2.  **Installez les dépendances :**

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

Avant de lancer l'application, vérifiez les fichiers de configuration :

  * **`kai_kite/config.yaml` :** Configurez les modèles de vision et les paramètres d'OCR.
  * **`kaitiaki/config/app.yaml` :** Configurez les chemins, les accès à Qdrant et au LLM.

## Guide de Démarrage Rapide

Suivez ces étapes pour ingérer vos documents et lancer l'application.

#### **Étape 1 : Ingestion des Données**

1.  **Ajoutez les documents :** Placez vos fichiers PDF dans `kaitiaki/data/raw/`.

2.  **Lancez `kai_kite` pour le parsing sémantique :**

    ```bash
    python -m kai_kite.main kaitiaki/data/raw/
    ```

3.  **Adaptez les sorties pour `kaitiaki` :**

    ```bash
    python -m kaitiaki.ingest.adapt_from_kaikite
    ```

4.  **Lancez l'indexation :**

    ```bash
    python -m kaitiaki.ingest.indexer
    ```

#### **Étape 2 : Lancement de l'Application**

1.  **Démarrez le serveur FastAPI :**

    ```bash
    uvicorn kaitiaki.api.server:app --reload
    ```

2.  **Accédez à l'interface :**

      * Ouvrez votre navigateur à l'adresse [http://127.0.0.1:8000](http://127.0.0.1:8000).

-----

### **Note sur le LLM en Développement**

L'objectif final de Kaitiaki est de fonctionner en circuit totalement fermé, avec un LLM hébergé localement pour une souveraineté complète.

Actuellement, la configuration par défaut utilise un endpoint externe (`ollama.com`). Il s'agit d'une **commodité temporaire pour le développement**, car mon Mac actuel n'est pas assez puissant pour faire tourner un modèle de 20 milliards de paramètres.

Le projet est à la recherche de sponsors : si vous souhaitez soutenir une solution de données souveraine pour la Nouvelle-Calédonie et pouvez proposer un **serveur local ou une machine de développement plus puissante**, votre aide serait la bienvenue pour atteindre cet objectif.

-----

## Avertissement

Kaitiaki a pour but de fournir des synthèses d'informations publiques. **Il ne constitue en aucun cas un avis juridique ou professionnel.** Les réponses doivent être vérifiées à l'aide des sources citées.

## Licence

Ce projet est sous licence MIT.