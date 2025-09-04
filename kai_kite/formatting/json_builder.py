# kai_kite/formatting/json_builder.py
import json
import uuid
from datetime import datetime

def build_final_json(source_file: str, extracted_elements: list):
    """
    Assemble les éléments extraits dans le format JSON final, en ajoutant
    des identifiants uniques et stables pour chaque chunk et chaque section.
    """
    
    current_title = ""
    current_section_id = None
    chunks = []

    # Trier les éléments par leur position (haut en bas) pour un ordre logique
    extracted_elements.sort(key=lambda x: (x.get('page', 0), x['coordinates'][1]))

    for element in extracted_elements:
        element_type = element['element_type']
        
        # Mettre à jour le titre et l'ID de la section courante
        if element_type in ["Title", "Section-header"]:
            current_title = element['content']
            current_section_id = str(uuid.uuid4()) # Nouvel ID pour chaque nouvelle section

        # Créer le chunk pour le JSON
        chunk = {
            "content": element['content'],
            "meta": {
                "chunk_id": str(uuid.uuid4()),
                "section_id": current_section_id,
                "doc_id": source_file,
                "page": element.get('page'),
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

