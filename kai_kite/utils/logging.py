# kai_kite/utils/logging.py
import logging
import sys

def setup_logger():
    """Configure et retourne un logger standard pour l'application."""
    logger = logging.getLogger("kai_tiaki")
    logger.setLevel(logging.INFO)

    # Eviter d'ajouter plusieurs handlers si la fonction est appelée plusieurs fois
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            '%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

# Créer une instance globale que les autres modules peuvent importer
logger = setup_logger()