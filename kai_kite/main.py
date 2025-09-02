# kai_kite/main.py
from pathlib import Path
import argparse
from kai_kite.core.pipeline import process_document
from kai_kite.utils.logging import logger

def main():
    """
    Point d'entrée de l'application.
    Analyse les arguments de la ligne de commande et lance le pipeline.
    """
    parser = argparse.ArgumentParser(description="Kai-tiaki: Traitement intelligent de documents.")
    parser.add_argument("input_file", type=str, help="Chemin vers le fichier à traiter.")
    args = parser.parse_args()

    input_path = Path(args.input_file)
    
    if not input_path.exists():
        logger.error(f"Le fichier '{input_path}' n'existe pas.")
        return

    process_document(input_path)

if __name__ == "__main__":
    main()
