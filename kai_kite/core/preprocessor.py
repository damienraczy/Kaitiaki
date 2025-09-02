# kai_kite/core/preprocessor.py
from pathlib import Path
from typing import List
from PIL import Image
import pymupdf  # fitz
from ..utils.logging import logger # <-- Importer le logger

# S'assurer que Pillow peut gérer des images de grande taille
Image.MAX_IMAGE_PIXELS = None

def get_images_from_file(file_path: Path, dpi: int = 300) -> List[Image.Image]:
    """
    Normalise un fichier d'entrée (PDF, JPG, PNG, TIFF) en une liste d'images Pillow.

    Args:
        file_path: Le chemin vers le fichier.
        dpi: La résolution à utiliser pour la conversion PDF -> image.

    Returns:
        Une liste d'objets PIL.Image.
        
    Raises:
        FileNotFoundError: Si le fichier n'existe pas.
        ValueError: Si le type de fichier n'est pas supporté.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Le fichier {file_path} n'a pas été trouvé.")

    suffix = file_path.suffix.lower()
    images = []

    if suffix == ".pdf":
        doc = pymupdf.open(file_path)
        for page_num, page in enumerate(doc):
            try:
                pix = page.get_pixmap(dpi=dpi)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)
            except Exception as e:
                logger.warning(f"Impossible de traiter la page {page_num} du PDF {file_path.name}. Erreur : {e}")
        doc.close()

    elif suffix in [".jpg", ".jpeg", ".png", ".bmp"]:
        try:
            img = Image.open(file_path).convert("RGB")
            images.append(img)
        except Exception as e:
            logger.warning(f"Impossible d'ouvrir l'image {file_path.name}. Erreur : {e}")

    elif suffix in [".tif", ".tiff"]:
        try:
            with Image.open(file_path) as img:
                for i in range(img.n_frames):
                    img.seek(i)
                    frame = img.copy().convert("RGB")
                    images.append(frame)
        except Exception as e:
            logger.warning(f"Impossible de traiter le TIFF {file_path.name}. Erreur : {e}")
            
    else:
        raise ValueError(f"Type de fichier non supporté : {suffix}")

    if not images:
        logger.warning(f"Aucun contenu image n'a pu être extrait de {file_path.name}.")
        
    return images