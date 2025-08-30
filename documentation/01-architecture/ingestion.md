# ingest

## parse
On parse les documents et on cherche à extraire les données de qualité, y compris les tableaux
Entrée : PDF, DOCX, TEXT, MD, BITMAP etc.
Sortie : JSON structuré décrivant le document, titres, paragraphes, tableaux, etc.

Outils : 
- PDF : pdfplumber + camelot
- DOCX : python-docx
- TEXT : markdown_it
- MD : markdown_it
- BITMAP : Azure



## normalize

Entrée: JSON contenant le document structuré
Sortie : JSON-LD avec le vocabulaire Dublin Core (éventuellement une ontologie pourra ultérieurement être utlisée)

## index

### Chunking
Effectue le "chunking" sémantique sur les blocs de contenu
Entrée : JSON-LD
Sortie : Haystack document

### Embedding
Entrée : Haystack Document
Sortie : vecteurs


# annexe

Format pibot por la sortie du parsin :
{
  "metadata": {
    "title": "Titre du document",
    "author": "Auteur si disponible",
    // ... autres métadonnées communes ...
  },
  "elements": [
    {
      "type": "title", // ou 'paragraph', 'table', 'list_item'
      "content": "Texte du titre",
      "level": 1, // Pour les titres (h1, h2...)
      "page_number": 1 
    },
    {
      "type": "paragraph",
      "content": "Ceci est un paragraphe de texte.",
      "page_number": 1
    },
    {
      "type": "table",
      "content": [  // Liste de dictionnaires (une par ligne)
        {"colonne_1": "cellule A1", "colonne_2": "cellule B1"},
        {"colonne_1": "cellule A2", "colonne_2": "cellule B2"}
      ],
      "page_number": 2
    }
  ]
}
