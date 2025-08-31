# kaitiaki/ingest/intelligent_parser.py
"""
Parsing intelligent avec préservation de la structure sémantique
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import pdfplumber
from kaitiaki.utils.settings import CFG

@dataclass
class DocumentElement:
    """Élément structuré d'un document"""
    type: str  # 'title', 'subtitle', 'paragraph', 'table', 'list_item', 'header'
    content: str
    metadata: Dict
    page: int
    position: int  # Position dans la page
    parent_section: Optional[str] = None
    semantic_context: Optional[str] = None

@dataclass
class TableCell:
    """Cellule de tableau avec contexte"""
    content: str
    row: int
    col: int
    column_header: Optional[str] = None
    row_header: Optional[str] = None

class IntelligentDocumentParser:
    """Parser qui préserve la structure sémantique"""
    
    def __init__(self):
        # Patterns pour identifier les structures
        self.title_patterns = [
            r'^[A-Z\s]{10,}$',  # TITRES EN MAJUSCULES
            r'^\s*CHAPITRE\s+[IVX\d]+',
            r'^\s*ARTICLE\s+[\d\w-]+',
            r'^\s*[IVX]+\.\s*[A-Z]',
        ]
        
        self.subtitle_patterns = [
            r'^\s*\d+\.\s*[A-Z]',  # 1. TITRE
            r'^\s*[a-z]\)\s*',     # a) sous-titre
            r'^\s*-\s*[A-Z]',      # - Titre
        ]
        
        # Patterns spéciaux pour documents salariaux
        self.salary_patterns = [
            r'GRILLE.*CLASSIFICATION',
            r'SALAIRE.*MINIMAL',
            r'BAREME.*SALAIRE',
            r'NIVEAU.*ECHELON',
            r'P\d+\s+E\d+',  # P2 E6
        ]

    def parse_pdf_intelligent(self, pdf_path: Path) -> List[DocumentElement]:
        """Parse un PDF en préservant la structure"""
        elements = []
        
        with pdfplumber.open(str(pdf_path)) as pdf:
            current_section = None
            
            for page_num, page in enumerate(pdf.pages, 1):
                # Extraire les tableaux séparément
                tables = page.extract_tables()
                
                # Extraire le texte avec positions
                text_elements = self._extract_text_with_structure(page)
                
                # Traiter les tableaux
                for table_idx, table in enumerate(tables):
                    if table and len(table) > 1:  # Au moins header + 1 ligne
                        table_elements = self._process_table_intelligent(
                            table, page_num, table_idx, pdf_path.name
                        )
                        elements.extend(table_elements)
                
                # Traiter le texte structuré
                for elem in text_elements:
                    if elem.type in ['title', 'subtitle']:
                        current_section = elem.content
                    elem.parent_section = current_section
                    elements.append(elem)
        
        return elements

    def _extract_text_with_structure(self, page) -> List[DocumentElement]:
        """Extrait le texte en identifiant la structure"""
        elements = []
        lines = page.extract_text().split('\n') if page.extract_text() else []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            element_type = self._classify_line(line)
            
            element = DocumentElement(
                type=element_type,
                content=line,
                metadata={'line_number': i},
                page=page.page_number,
                position=i
            )
            
            elements.append(element)
        
        return elements

    def _classify_line(self, line: str) -> str:
        """Classifie une ligne de texte selon sa structure"""
        # Titres principaux
        for pattern in self.title_patterns:
            if re.match(pattern, line):
                return 'title'
        
        # Sous-titres  
        for pattern in self.subtitle_patterns:
            if re.match(pattern, line):
                return 'subtitle'
        
        # Éléments de liste
        if re.match(r'^\s*[-•]\s*', line):
            return 'list_item'
        
        # Contenu spécialisé salaires
        for pattern in self.salary_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return 'salary_info'
        
        return 'paragraph'

    def _process_table_intelligent(self, table: List[List], page_num: int, 
                                 table_idx: int, doc_name: str) -> List[DocumentElement]:
        """Traite un tableau en préservant la sémantique"""
        elements = []
        
        if not table or len(table) < 2:
            return elements
        
        # Identifier les headers
        headers = table[0] if table[0] else []
        
        # Cas spécial : grille salariale BTP
        if self._is_salary_table(table, doc_name):
            elements.extend(self._process_salary_table(table, page_num, table_idx))
        else:
            # Traitement générique
            elements.extend(self._process_generic_table(table, page_num, table_idx))
        
        return elements

    def _is_salary_table(self, table: List[List], doc_name: str) -> bool:
        """Détecte si c'est une grille salariale"""
        doc_indicators = ['salaire', 'btp', 'travaux', 'publics']
        table_content = ' '.join([' '.join(row) for row in table[:2]]).lower()
        
        return (any(indicator in doc_name.lower() for indicator in doc_indicators) and
                any(term in table_content for term in ['niveau', 'echelon', 'xpf', 'salaire']))

    def _process_salary_table(self, table: List[List], page_num: int, 
                            table_idx: int) -> List[DocumentElement]:
        """Traitement spécialisé pour les grilles salariales"""
        elements = []
        
        # Créer un élément englobant pour le tableau
        table_summary = self._create_salary_table_summary(table)
        elements.append(DocumentElement(
            type='salary_table',
            content=table_summary,
            metadata={'table_idx': table_idx, 'is_salary_grid': True},
            page=page_num,
            position=0,
            semantic_context="Grille salariale BTP avec niveaux et échelons"
        ))
        
        # Traiter chaque ligne avec enrichissement sémantique
        for row_idx, row in enumerate(table[1:], 1):  # Skip header
            if not any(cell for cell in row if cell):  # Skip empty rows
                continue
                
            row_content = self._enrich_salary_row(row, table[0] if table[0] else [])
            if row_content:
                elements.append(DocumentElement(
                    type='salary_row',
                    content=row_content,
                    metadata={
                        'table_idx': table_idx,
                        'row_idx': row_idx,
                        'original_row': row
                    },
                    page=page_num,
                    position=row_idx,
                    semantic_context="Détail niveau salarial BTP"
                ))
        
        return elements

    def _create_salary_table_summary(self, table: List[List]) -> str:
        """Crée un résumé sémantique du tableau salarial"""
        summary_parts = [
            "GRILLE SALARIALE BTP - Salaires minimaux hiérarchiques",
            "Niveaux: I, II, III, IV, V avec échelons 1er, 2ème, 3ème",
            "Categories: Ouvriers (O), Employés (E), Techniciens (T), Agents de maîtrise (AM)",
            "Codes salariaux: P1, P2, P3 (ouvriers qualifiés), HQ (haute qualification)"
        ]
        
        # Extraire les salaires présents
        salaries_found = []
        for row in table:
            for cell in row:
                if cell and re.search(r'\d{3,}\s*(?:XPF|F\.?CFP)', str(cell)):
                    salaries_found.append(str(cell).strip())
        
        if salaries_found:
            summary_parts.append(f"Salaires mentionnés: {', '.join(set(salaries_found))}")
        
        return '\n'.join(summary_parts)

    def _enrich_salary_row(self, row: List, headers: List) -> str:
        """Enrichit une ligne de salaire avec du contexte sémantique"""
        if not any(cell for cell in row if cell):
            return ""
        
        enriched_parts = []
        
        # Traitement spécial selon les patterns détectés
        row_text = ' '.join([str(cell) for cell in row if cell])
        
        # Détecter les codes de niveau (P1, P2, P3, etc.)
        level_codes = re.findall(r'[PO]\d+', row_text)
        if level_codes:
            enriched_parts.append(f"NIVEAU SALARIAL: {', '.join(level_codes)}")
            for code in level_codes:
                if code.startswith('P'):
                    enriched_parts.append(f"Code {code} = Ouvrier qualifié niveau {code[1:]}")
                elif code.startswith('O'):
                    enriched_parts.append(f"Code {code} = Ouvrier niveau {code[1:]}")
        
        # Détecter les salaires
        salaries = re.findall(r'(\d{3,}(?:\s*\d{3})*)\s*(?:XPF|F\.?CFP)?', row_text)
        if salaries:
            enriched_parts.append(f"SALAIRES: {', '.join(salaries)} XPF")
        
        # Détecter les échelons
        if re.search(r'(?:1ER|2EME|3EME|\d+EME)', row_text):
            echelon_match = re.search(r'(1ER|2EME|3EME|\d+EME)', row_text)
            if echelon_match:
                enriched_parts.append(f"ECHELON: {echelon_match.group(1)}")
        
        # Contenu original
        enriched_parts.append(f"CONTENU ORIGINAL: {row_text}")
        
        return '\n'.join(enriched_parts)

    def _process_generic_table(self, table: List[List], page_num: int, 
                             table_idx: int) -> List[DocumentElement]:
        """Traitement générique des tableaux"""
        elements = []
        
        headers = table[0] if table[0] else []
        
        for row_idx, row in enumerate(table[1:], 1):
            if not any(cell for cell in row if cell):
                continue
            
            # Créer un contenu contextualisé
            row_content = self._contextualize_table_row(row, headers)
            
            elements.append(DocumentElement(
                type='table_row',
                content=row_content,
                metadata={
                    'table_idx': table_idx,
                    'row_idx': row_idx,
                    'headers': headers
                },
                page=page_num,
                position=row_idx
            ))
        
        return elements

    def _contextualize_table_row(self, row: List, headers: List) -> str:
        """Contextualise une ligne de tableau avec ses headers"""
        contextualized = []
        
        for i, (cell, header) in enumerate(zip(row, headers)):
            if cell and str(cell).strip():
                if header and str(header).strip():
                    contextualized.append(f"{header}: {cell}")
                else:
                    contextualized.append(str(cell))
        
        return ' | '.join(contextualized)

def create_intelligent_chunks(elements: List[DocumentElement], 
                           chunk_size: int = 1500, 
                           overlap: int = 300) -> List[Dict]:
    """Crée des chunks intelligents préservant la sémantique"""
    chunks = []
    current_chunk = []
    current_size = 0
    current_section = None
    
    for element in elements:
        element_text = element.content
        element_size = len(element_text)
        
        # Si changement de section ou chunk trop gros
        if (current_section != element.parent_section or 
            current_size + element_size > chunk_size) and current_chunk:
            
            # Finaliser le chunk actuel
            chunk_content = '\n'.join(current_chunk)
            chunks.append({
                'text': chunk_content,
                'doc_id': 'unknown',  # À définir par l'appelant
                'page': element.page,
                'section': current_section,
                'types': list(set([elem.type for elem in current_chunk if hasattr(elem, 'type')])),
                'semantic_context': current_section
            })
            
            # Commencer nouveau chunk avec overlap
            if overlap > 0 and current_chunk:
                overlap_text = '\n'.join(current_chunk[-2:])  # 2 derniers éléments
                current_chunk = [overlap_text, element_text]
                current_size = len(overlap_text) + element_size
            else:
                current_chunk = [element_text]
                current_size = element_size
        else:
            current_chunk.append(element_text)
            current_size += element_size
        
        current_section = element.parent_section
    
    # Finaliser le dernier chunk
    if current_chunk:
        chunk_content = '\n'.join(current_chunk)
        chunks.append({
            'text': chunk_content,
            'doc_id': 'unknown',
            'page': elements[-1].page if elements else 1,
            'section': current_section,
            'types': ['mixed'],
            'semantic_context': current_section
        })
    
    return chunks

# ========================================
# INTEGRATION DANS LE PIPELINE EXISTANT
# ========================================

def parse_pdf_intelligent_main(pdf_path: Path) -> Dict[Unknown, Unknown]:
    """Point d'entrée principal pour le parsing intelligent"""
    parser = IntelligentDocumentParser()
    
    # Parse avec structure
    elements = parser.parse_pdf_intelligent(pdf_path)
    
    # Créer les chunks intelligents
    chunks_data = create_intelligent_chunks(elements)
    
    # Enrichir avec metadata du document
    for chunk in chunks_data:
        chunk['doc_id'] = pdf_path.name
        chunk['source'] = 'AUTO'  # TODO: détecter JONC/IEOM/ISEE
        chunk['date'] = 'AUTO'    # TODO: extraire date
    
    return {
        'doc_id': pdf_path.name,
        'elements': [elem.__dict__ for elem in elements],  # Pour debug
        'chunks': chunks_data
    }

if __name__ == "__main__":
    # Test sur le document problématique
    test_file = Path("kaitiaki/data/raw/20191021cdsp_batiments_et_travaux_publics_salaire_conventionnel.pdf")
    if test_file.exists():
        result = parse_pdf_intelligent_main(test_file)
        print(f"Document: {result['doc_id']}")
        print(f"Chunks créés: {len(result['chunks'])}")
        
        # Afficher les chunks pour diagnostic
        for i, chunk in enumerate(result['chunks'][:3]):
            print(f"\n=== CHUNK {i+1} ===")
            print(f"Section: {chunk.get('section', 'N/A')}")
            print(f"Types: {chunk.get('types', [])}")
            print(f"Taille: {len(chunk['text'])} chars")
            print(f"Aperçu: {chunk['text'][:200]}...")