# kai_kite/main.py
from pathlib import Path
import argparse
from kai_kite.core.pipeline import process_document
from kai_kite.utils.logging import logger
import yaml

def main():
    """
    Point d'entrée de l'application.
    Analyse les arguments de la ligne de commande et lance le pipeline
    sur un ou plusieurs fichiers.
    """
    parser = argparse.ArgumentParser(description="Kai-kite: Traitement intelligent de documents.")
    parser.add_argument(
        "input_path",
        type=str,
        help="Chemin vers le fichier ou le dossier à traiter."
    )
    args = parser.parse_args()

    input_path = Path(args.input_path)

    if not input_path.exists():
        logger.error(f"Le chemin '{input_path}' n'existe pas.")
        return

    # Déterminer les fichiers à traiter
    files_to_process = []
    if input_path.is_dir():
        # Le chemin est un dossier, on prend tous les fichiers supportés
        supported_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']
        for ext in supported_extensions:
            files_to_process.extend(input_path.glob(f'*{ext}'))
        logger.info(f"{len(files_to_process)} document(s) trouvé(s) dans le dossier '{input_path}'.")
    elif input_path.is_file():
        # Le chemin est un fichier unique
        files_to_process.append(input_path)
    else:
        logger.error(f"Le chemin '{input_path}' n'est ni un fichier ni un dossier valide.")
        return

    # Traiter chaque fichier
    for file_path in files_to_process:
        # try:
        logger.info(f"--- Début du traitement pour le fichier : {file_path.name} ---")
        process_document(file_path)
        logger.info(f"--- Fin du traitement pour le fichier : {file_path.name} ---")
        # except Exception as e:
        #     logger.error(f"Une erreur est survenue lors du traitement de {file_path.name}: {e}")

if __name__ == "__main__":
    main()