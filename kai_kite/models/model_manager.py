# kai_kite/models/model_manager.py
from ultralytics import YOLO
from transformers import TableTransformerForObjectDetection, AutoImageProcessor
from ..utils.config import get_config
from ..utils.logging import logger # <-- Importer le logger

def get_layout_model():
    # ... (code existant)
    config = get_config()
    model_path = config['models']['layout_detector']['repo_id']
    logger.info(f"Chargement du modèle : {model_path}...")
    model = YOLO(model_path)
    logger.info("Modèle chargé avec succès.")
    return model

def get_table_models():
    """Charge et retourne les modèles TATR et leur processeur d'image."""
    config = get_config()
    structure_repo_id = config['models']['table_transformer']['structure_repo_id']
    
    logger.info(f"Chargement du modèle de structure de tableau : {structure_repo_id}...")
    
    image_processor = AutoImageProcessor.from_pretrained(structure_repo_id)
    model = TableTransformerForObjectDetection.from_pretrained(structure_repo_id)
    
    logger.info("Modèles de tableau chargés avec succès.")
    return image_processor, model