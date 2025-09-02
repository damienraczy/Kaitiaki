# kai_kite/core/pipeline.py
from pathlib import Path
import json

from pathlib import Path
import json
from .layout_detector import detect_layout
from .content_extractor import extract_content_from_boxes # <-- Changement de nom
from ..formatting.json_builder import build_final_json
from .preprocessor import get_images_from_file
from ..utils.logging import logger
from ..utils.config import get_config
from kai_kite.models.model_manager import get_layout_model, get_table_models # <-- Importer les fonctions

layout_model = None
table_model = None
table_image_processor = None

def process_document(file_path: Path):
    """Pipeline complet pour traiter un document."""

    global layout_model, table_model, table_image_processor

    if layout_model is None:
        layout_model = get_layout_model()
    if table_model is None or table_image_processor is None:
        table_image_processor, table_model = get_table_models()

    # --- Lire la configuration ---
    config = get_config()
    conf_threshold = config['processing']['detection_confidence_threshold']
    dpi = config['processing']['image_dpi']
    
    output_json_path = Path("data/processed") / f"{file_path.stem}.json"
    
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

        # Étape 1 : Détection de la mise en page (inchangée)
        detected_boxes = detect_layout(page_image, layout_model)
        
        # Étape 2 : Extraction du contenu pour toutes les boîtes (OPTIMISÉ)
        page_elements = extract_content_from_boxes(
            page_image,
            detected_boxes,
            layout_model,
            conf_threshold,
            (table_image_processor, table_model)
        )
        
        # Ajouter le numéro de page aux éléments extraits
        for element in page_elements:
            element["page"] = page_num + 1
        
        extracted_elements.extend(page_elements)
    
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
