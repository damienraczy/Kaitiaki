# kai_kite/core/content_extractor.py
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="torch.nn.modules.module")

from PIL import Image
import pytesseract
import torch

def extract_content_from_boxes(page_image: Image.Image, detected_boxes, layout_model, conf_threshold, table_models) -> list:
    """
    Extrait le contenu (texte ou tableau) de toutes les boîtes détectées sur une page.
    OPTIMISÉ : L'OCR est fait une seule fois pour toute la page.
    """
    extracted_elements = []
    
    # --- OPTIMISATION : Exécuter l'OCR une seule fois sur toute la page ---
    try:
        ocr_data = pytesseract.image_to_data(page_image, lang='fra', output_type=pytesseract.Output.DICT)
    except pytesseract.TesseractNotFoundError:
        print("\n\nERREUR CRITIQUE : Tesseract n'est pas installé ou n'est pas dans le PATH.")
        raise
    except Exception as e:
        print(f"Une erreur est survenue pendant l'OCR de la page : {e}")
        ocr_data = None # On continue sans OCR si une erreur survient
    # --------------------------------------------------------------------

    table_image_processor, table_model = table_models

    for box in detected_boxes:
        if float(box.conf[0]) < conf_threshold:
            continue

        class_name = layout_model.names[int(box.cls[0])]
        coords = box.xyxy[0].tolist()
        content = ""

        if class_name in ["Text", "Title", "Section-header", "List-item"]:
            # On utilise les données de l'OCR global
            content = _get_text_in_box(ocr_data, coords)
        elif class_name == "Table":
            # L'extraction de tableau reste une opération sur une image rognée
            content = _extract_table_from_box(page_image, coords, table_image_processor, table_model)
        elif class_name == "Picture" :
            print(f"### class_name non traité : <<<---{class_name}--->>>")
        elif class_name == "Page-header" :
            content = _get_text_in_box(ocr_data, coords)
        elif class_name == "Page-footer" :
            content = _get_text_in_box(ocr_data, coords)
        else :
            print(f"### class_name OUBLIÉ : <<<---{class_name}--->>>")

        if content:
            extracted_elements.append({
                # "page" sera ajouté dans le pipeline principal
                "element_type": class_name,
                "confidence": float(box.conf[0]),
                "coordinates": coords,
                "content": content
            })
            
    return extracted_elements


def _get_text_in_box(ocr_data: dict, box_coords: list) -> str:
    """
    Helper qui assemble le texte présent à l'intérieur d'une boîte
    à partir des données OCR de la page entière.
    """
    if not ocr_data:
        return ""
        
    x1, y1, x2, y2 = box_coords
    text_parts = []
    
    for i in range(len(ocr_data['text'])):
        # On ne garde que les mots avec une confiance suffisante
        if int(ocr_data['conf'][i]) > 60:
            # Coordonnées du mot trouvé par l'OCR
            w_x, w_y, w_w, w_h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
            
            # On calcule le centre du mot
            word_center_x = w_x + w_w / 2
            word_center_y = w_y + w_h / 2
            
            # Si le centre du mot est dans notre boîte, on le garde
            if (x1 < word_center_x < x2) and (y1 < word_center_y < y2):
                text_parts.append(ocr_data['text'][i])
                
    return " ".join(text_parts).strip()

def _extract_table_from_box(page_image: Image.Image, box_coords: list, image_processor, model) -> str:
    """
    (Version OPTIMISÉE) Extrait la structure d'un tableau.
    L'OCR est fait une seule fois sur l'image du tableau.
    """
    try:
        table_image = page_image.crop(box_coords)
        
        # --- L'OCR est fait une seule fois sur l'image du tableau ---
        try:
            table_ocr_data = pytesseract.image_to_data(table_image, lang='fra', output_type=pytesseract.Output.DICT)
        except Exception as ocr_error:
            print(f"Avertissement : Erreur OCR sur un tableau : {ocr_error}")
            table_ocr_data = None
        # -----------------------------------------------------------

        inputs = image_processor(images=table_image, return_tensors="pt")
        outputs = model(**inputs)
        target_sizes = torch.tensor([table_image.size[::-1]])
        results = image_processor.post_process_object_detection(outputs, threshold=0.7, target_sizes=target_sizes)[0]

        cells = []
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            cell_coords = [round(i, 2) for i in box.tolist()]
            
            # On utilise les données de l'OCR du tableau pour extraire le texte de la cellule
            cell_text = _get_text_in_box(table_ocr_data, cell_coords)
            
            cells.append({'box': cell_coords, 'text': cell_text})

        return _linearize_table(cells)
        
    except Exception as e:
        print(f"Erreur lors de l'extraction du tableau : {e}")
        return ""

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
