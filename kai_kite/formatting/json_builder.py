# kai_kite/formatting/json_builder.py
import json
from datetime import datetime

def build_final_json(source_file: str, extracted_elements: list):
    """
    Assemble les éléments extraits dans le format JSON final pour le RAG.

    Args:
        source_file: Le nom du fichier original.
        extracted_elements: Une liste de dictionnaires, chaque dict représentant un élément.
    """
    
    # On ajoute un peu de logique pour hériter le titre de la section
    current_title = ""
    chunks = []

    # Trier les éléments par leur position (haut en bas) pour un ordre logique
    extracted_elements.sort(key=lambda x: x['coordinates'][1])

    for element in extracted_elements:
        element_type = element['element_type']
        
        # Mettre à jour le titre de la section courante
        if element_type in ["Title", "Section-header"]:
            current_title = element['content']

        # Créer le chunk pour le JSON
        chunk = {
            "content": element['content'],
            "meta": {
                "doc_id": source_file,
                "page": element['page'],
                "element_type": element_type,
                "parent_title": current_title if current_title != element['content'] else "",
                "coordinates": element['coordinates']
            }
        }
        chunks.append(chunk)

    final_structure = {
        "source_file": source_file,
        "processing_date": datetime.utcnow().isoformat() + "Z",
        "chunks": chunks
    }
    
    return final_structure