# kai_kite/core/pipeline.py
from pathlib import Path
import json

from ..utils.logging import logger # <-- Importer le logger
from ..utils.config import get_config
from ..models.model_manager import get_layout_model, get_table_models
from .layout_detector import detect_layout
from .content_extractor import extract_text_from_box, extract_table_from_box
from ..formatting.json_builder import build_final_json
from .preprocessor import get_images_from_file

def process_document(file_path: Path):
    """Pipeline complet pour traiter un document."""
    
    # --- Lire la configuration ---
    config = get_config()
    conf_threshold = config['processing']['detection_confidence_threshold']
    dpi = config['processing']['image_dpi']
    
    output_json_path = Path("data/processed") / f"{file_path.stem}.json"
    
    logger.info("Chargement des modèles...")
    layout_model = get_layout_model()
    table_image_processor, table_model = get_table_models()
    
    extracted_elements = []
    
    logger.info(f"Prétraitement du document : {file_path.name}")
    try:
        page_images = get_images_from_file(file_path, dpi=dpi)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Erreur critique : {e}")
        return

    logger.info(f"Traitement de {len(page_images)} page(s)...")
    for page_num, page_image in enumerate(page_images):
        logger.info(f"  - Traitement de la page {page_num + 1}/{len(page_images)}")

        detected_boxes = detect_layout(page_image, layout_model)
        
        for box in detected_boxes:
            if float(box.conf[0]) < conf_threshold: continue

            class_name = layout_model.names[int(box.cls[0])]
            coords = box.xyxy[0].tolist()
            content = ""

            if class_name in ["Text", "Title", "Section-header", "List-item"]:
                content = extract_text_from_box(page_image, coords)
            elif class_name == "Table":
                content = extract_table_from_box(page_image, coords, table_image_processor, table_model)
            
            if content:
                extracted_elements.append({
                    "page": page_num + 1,
                    "element_type": class_name,
                    "confidence": float(box.conf[0]),
                    "coordinates": coords,
                    "content": content
                })
    
    if not extracted_elements:
        logger.warning("Aucun contenu n'a été extrait. Le fichier JSON ne sera pas généré.")
        return

    logger.info("Assemblage du JSON final...")
    final_json_data = build_final_json(file_path.name, extracted_elements)
    
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(final_json_data, f, ensure_ascii=False, indent=2)
        
    logger.info("Traitement terminé !")
    logger.info(f"Fichier de sortie généré ici : {output_json_path}")