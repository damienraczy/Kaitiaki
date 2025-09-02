# kai_kite/core/content_extractor.py
from PIL import Image
import pytesseract
import torch

def extract_text_from_box(page_image: Image.Image, box_coords: list) -> str:
    """
    Extrait le texte d'une zone spécifique (boîte) d'une image en utilisant l'OCR.

    Args:
        page_image: L'image complète de la page (objet Pillow).
        box_coords: Les coordonnées [x1, y1, x2, y2] de la boîte.

    Returns:
        Le texte extrait.
    """
    try:
        # 1. Recadrer l'image pour n'isoler que la zone de la boîte
        cropped_image = page_image.crop(box_coords)

        # 2. Utiliser pytesseract pour faire l'OCR
        # On ajoute des options de configuration pour aider Tesseract
        custom_config = r'--oem 3 --psm 6 -l fra'
        text = pytesseract.image_to_string(cropped_image, config=custom_config)
        return text.strip()

    except pytesseract.TesseractNotFoundError:
        print("\n\nERREUR CRITIQUE : Tesseract n'est pas installé ou n'est pas dans le PATH système.")
        print("Sur macOS avec Homebrew, assurez-vous d'avoir bien fait 'brew install tesseract'.")
        print("Sur d'autres systèmes, vérifiez votre installation.\n\n")
        # On arrête le programme pour que l'erreur soit bien visible
        raise 
    except Exception as e:
        # Pour les autres erreurs (ex: pack de langue manquant)
        print(f"Une erreur est survenue pendant l'OCR : {e}")
        return ""

def extract_table_from_box(page_image: Image.Image, box_coords: list, image_processor, model) -> str:
    """
    Extrait la structure d'un tableau et la convertit en Markdown.

    Args:
        page_image: L'image complète de la page.
        box_coords: Les coordonnées du tableau détecté par YOLO.
        image_processor: Le processeur d'image pour TATR.
        model: Le modèle TATR.

    Returns:
        Une chaîne de caractères représentant le tableau au format Markdown.
    """
    try:
        # 1. Recadrer l'image sur la zone du tableau
        table_image = page_image.crop(box_coords)
        # 2. Préparer l'image pour le modèle
        inputs = image_processor(images=table_image, return_tensors="pt")
        # 3. Faire l'inférence
        outputs = model(**inputs)
        # 4. Convertir les résultats en une structure de données
        target_sizes = torch.tensor([table_image.size[::-1]])
        results = image_processor.post_process_object_detection(outputs, threshold=0.7, target_sizes=target_sizes)[0]

        # 5. Extraire le texte de chaque cellule détectée
        cells = []
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            cell_coords = [round(i, 2) for i in box.tolist()]
            # Appliquer l'OCR sur chaque cellule
            cell_text = extract_text_from_box(table_image, cell_coords)
            cells.append({'box': cell_coords, 'text': cell_text})


        # --- NOUVELLE LOGIQUE DE RECONSTRUCTION ---
        return _linearize_table(cells)
        # 6. Reconstruire le tableau et le convertir en Markdown
        # markdown_table = _reconstruct_table_to_markdown(cells)
        # return markdown_table

    except Exception as e:
        print(f"Erreur lors de l'extraction du tableau : {e}")
        return ""

def _reconstruct_table_to_markdown(cells: list) -> str:
    """Helper pour convertir une liste de cellules en tableau Markdown."""
    if not cells:
        return ""
    
    # Estimer le nombre de lignes et de colonnes en se basant sur les positions
    # (Ceci est une simplification, une logique plus robuste serait nécessaire pour les cellules fusionnées)
    rows = {}
    for cell in cells:
        # Utiliser le centre vertical de la cellule pour l'assigner à une ligne
        y_center = (cell['box'][1] + cell['box'][3]) / 2
        # Trouver une ligne existante proche ou en créer une nouvelle
        found_row = False
        for row_y in rows:
            if abs(y_center - row_y) < 20: # Seuil de tolérance
                rows[row_y].append(cell)
                found_row = True
                break
        if not found_row:
            rows[y_center] = [cell]

    # Trier les lignes par position verticale, et les cellules de chaque ligne par position horizontale
    sorted_rows = sorted(rows.items(), key=lambda item: item[0])
    
    md = []
    header_separator_added = False
    for _, row_cells in sorted_rows:
        sorted_cells = sorted(row_cells, key=lambda cell: cell['box'][0])
        # Remplacer les sauts de ligne dans les cellules pour ne pas casser le Markdown
        row_text = [cell['text'].replace('\n', ' ').replace('|', '\|') for cell in sorted_cells]
        md.append("| " + " | ".join(row_text) + " |")
        
        # Ajouter la ligne de séparation de l'en-tête après la première ligne
        if not header_separator_added:
            separator = "| " + " | ".join(["---"] * len(row_cells)) + " |"
            md.append(separator)
            header_separator_added = True
            
    return "\n".join(md)


def _linearize_table(cells: list) -> str:
    """Helper pour convertir une liste de cellules en une chaîne de caractères structurée."""
    if not cells:
        return ""
    
    # Grouper les cellules par ligne en se basant sur leur position verticale
    rows = {}
    for cell in cells:
        y_center = (cell['box'][1] + cell['box'][3]) / 2
        found_row = False
        for row_y in rows:
            if abs(y_center - row_y) < 20: # Seuil de tolérance
                rows[row_y].append(cell)
                found_row = True
                break
        if not found_row:
            rows[y_center] = [cell]

    # Trier les lignes et les cellules, puis formater la sortie
    sorted_rows = sorted(rows.items(), key=lambda item: item[0])
    
    linearized_text = ""
    for _, row_cells in sorted_rows:
        sorted_cells = sorted(row_cells, key=lambda cell: cell['box'][0])
        row_text = " | ".join([cell['text'].replace('\n', ' ') for cell in sorted_cells])
        linearized_text += f"Ligne : [ {row_text} ]\n"
            
    return linearized_text.strip()
