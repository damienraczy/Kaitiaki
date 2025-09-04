### **Documentation : `kai_kite` – Moteur d'Ingestion Intelligente**

#### **Rôle dans le Processus Global**

`kai_kite` est la **première étape** et le moteur d'ingestion de données du système Kaitiaki. Son unique responsabilité est de transformer des documents bruts (PDF, images) en une représentation JSON structurée et sémantique.

Il remplace les anciens scripts de parsing basique en utilisant des modèles de vision par ordinateur pour comprendre la mise en page des documents, offrant une qualité d'extraction bien supérieure, notamment pour les documents complexes avec des tableaux et plusieurs colonnes.

#### **Architecture et Modèles Utilisés**

`kai_kite` adopte une approche "vision-first" : il traite les pages de document comme des images pour en analyser la structure avant d'en extraire le texte.

Les modèles suivants sont au cœur de son fonctionnement :

1.  **Détecteur de Mise en Page (YOLOv10)** :

      * **Rôle :** Analyse l'image de chaque page pour identifier et délimiter les zones logiques : titres (`Title`), paragraphes (`Text`), tableaux (`Table`), listes (`List-item`), etc.

2.  **Reconnaissance de Tableaux (Table Transformer)** :

      * **Rôle :** Lorsqu'une zone est identifiée comme un tableau, ce modèle spécialisé analyse sa structure interne (cellules, lignes, colonnes) pour permettre une extraction correcte des données.

3.  **Reconnaissance de Caractères (Tesseract OCR)** :

      * **Rôle :** Intervient après la détection de structure pour "lire" le contenu textuel à l'intérieur des zones identifiées par les modèles précédents.

#### **Flux de Données (Data Flow)**

Le traitement d'un document suit un pipeline linéaire et séquentiel :

1.  **Entrée :** Un fichier (ex: `.pdf`) est lu depuis le dossier `kaitiaki/data/raw/`.
2.  **Prétraitement (`preprocessor.py`) :** Le fichier est converti en une série d'images en haute résolution, une pour chaque page.
3.  **Détection de Layout (`layout_detector.py`) :** Pour chaque image de page, le modèle YOLO est appliqué et retourne une liste de "boîtes englobantes" (bounding boxes) avec leurs labels (ex: "Table", "Text").
4.  **Extraction de Contenu (`content_extractor.py`) :** Pour chaque boîte détectée sur la page :
      * L'OCR est appliqué sur la page entière pour extraire tout le texte.
      * Le texte correspondant à la boîte est extrait des données OCR.
      * Si la boîte est un tableau, le Table Transformer est appelé pour en extraire la structure et le contenu de manière linéarisée.
5.  **Formatage (`json_builder.py`) :** Tous les éléments extraits (texte des paragraphes, contenu des tableaux, etc.) sont assemblés en un unique fichier JSON.
6.  **Sortie :** Le fichier final (ex: `mon_document.json`) est sauvegardé dans `kaitiaki/data/processed/`. Ce fichier contient une liste de "chunks" sémantiques, prêts à être utilisés par `kaitiaki`.

#### **Commandes d'Exécution**

Pour lancer le processus `kai_kite` sur l'ensemble des documents, une seule commande est nécessaire depuis la racine du projet :

```bash
# Lance le traitement sur tous les fichiers du dossier kaitiaki/data/raw/
python -m kai_kite.main kaitiaki/data/raw/
```

Cette commande va automatiquement trouver les fichiers, les traiter un par un, et générer les fichiers JSON correspondants dans le dossier `kaitiaki/data/processed/`, qui serviront d'entrée pour la phase suivante du pipeline Kaitiaki.