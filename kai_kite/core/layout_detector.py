# kai_kite/core/layout_detector.py
from PIL import Image

def detect_layout(page_image: Image.Image, layout_model):
    """
    Détecte les éléments de mise en page sur une image en utilisant un modèle YOLO.

    Args:
        page_image: L'image de la page à analyser.
        layout_model: Le modèle YOLO chargé.

    Returns:
        Les boîtes de détection (un objet `ultralytics.engine.results.Boxes`).
    """
    results = layout_model(page_image)
    return results[0].boxes