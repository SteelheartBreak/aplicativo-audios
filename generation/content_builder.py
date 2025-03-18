"""
Módulo para la construcción del informe final en diferentes formatos.

Este módulo contiene funciones para tomar el contenido generado por IA
y construir documentos finales en diferentes formatos (Markdown, HTML, DOCX).
"""

import os
import json
import re
import datetime
from typing import Dict, List, Any, Optional, Tuple

# Intentar importar librerias para generación de documentos
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    print("Advertencia: python-markdown no está instalado. No se podrá convertir a HTML.")
    print("Para instalar: pip install markdown")

try:
    from docx import Document
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("Advertencia: python-docx no está instalado. No se podrá generar DOCX.")
    print("Para instalar: pip install python-docx")


def extract_sections_hierarchy(structure: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extrae jerarquía de secciones manteniendo estructura original.
    
    Args:
        structure (dict): Estructura del informe.
        
    Returns:
        list: Lista de secciones con su jerarquía intacta.
    """
    return structure['secciones'].copy()


def find_section_content(section_id: str, generated_content: Dict[str, Dict[str, Any]]) -> Optional[str]:
    """
    Busca el contenido generado para una sección específica.
    
    Args:
        section_id (str): ID de la sección.
        generated_content (dict): Diccionario con contenido generado.
        
    Returns:
        str or None: Contenido generado o None si no existe.
    """
    if section_id in generated_content:
        return generated_content[section_id].get('contenido_generado', "")
    return None


def process_section_for_markdown(section: Dict[str, Any], 
                              generated_content: Dict[str, Dict[str, Any]], 
                              level: int = 1) -> Tuple[str, bool]:
    """
    Procesa una sección para formato Markdown.
    
    Args:
        section (dict): Información de la sección.
        generated_content (dict): Diccionario con contenido generado.
        level (int): Nivel de la sección (para determinar encabezados).
        
    Returns:
        tuple: (texto markdown, flag indicando si hay contenido)
    """
    # Buscar contenido para esta sección
    content = find_section_content(section['id'], generated_content)
    has_content = content is not None and content.strip() != ""
    
    # Crear encabezado según nivel
    header_level = "#" * (level + 1)  # Nivel base + 1 para que título principal sea h2
    markdown_text = f"{header_level} {section['titulo']}\n\n"
    
    # Añadir contenido si existe
    if has_content:
        markdown_text += f"{content}\n\n"
    else:
        markdown_text += "*No se ha generado contenido para esta sección.*\n\n"
    
    # Procesar subsecciones recursivamente
    if 'subsecciones' in section and section['subsecciones']:
        for subsection in section['subsecciones']:
            sub_text, sub_has_content = process_section_for_markdown(
                subsection, generated_content, level + 1
            )
            markdown_text += sub_text
            has_content = has_content or sub_has_content
    
    return markdown_text, has_content


def generate_markdown_report(hierarchy: List[Dict[str, Any]], 
                           generated_content: Dict[str, Dict[str, Any]]) -> str:
    """
    Genera un informe en formato Markdown.
    
    Args:
        hierarchy (list): Jerarquía de secciones.
        generated_content (dict): Diccionario con contenido generado.
        
    Returns:
        str: Documento Markdown completo.
    """
    # Metadata y título
    now = datetime.datetime.now()
    markdown_text = f"""---
title: Línea Base - Informe Ambiental
date: {now.strftime('%Y-%m-%d')}
author: Sistema de Generación Automática de Informes
---

# Línea Base - Informe Ambiental

*Documento generado automáticamente el {now.strftime('%d de %B de %Y')}*

"""
    
    # Procesar secciones principales
    for section in hierarchy:
        section_text, _ = process_section_for_markdown(section, generated_content)
        markdown_text += section_text
    
    # Añadir pie de página
    markdown_text += """
---

*Este documento ha sido generado automáticamente a partir de transcripciones procesadas
con técnicas de procesamiento de lenguaje natural e inteligencia artificial.*
"""
    
    return markdown_text


def generate_html_report(markdown_text: str) -> Optional[str]:
    """
    Convierte un informe Markdown a HTML.
    
    Args:
        markdown_text (str): Texto en formato Markdown.
        
    Returns:
        str or None: Documento HTML o None si no está disponible.
    """
    if not MARKDOWN_AVAILABLE:
        return None
    
    # Convertir Markdown a HTML
    html = markdown.markdown(markdown_text, extensions=['tables', 'fenced_code'])
    
    # Añadir estilos básicos
    html_document = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Línea Base - Informe Ambiental</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #2c5282;
            margin-top: 1.5em;
        }}
        h1 {{
            text-align: center;
            border-bottom: 2px solid #2c5282;
            padding-bottom: 10px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        code {{
            background-color: #f5f5f5;
            padding: 2px 4px;
            border-radius: 4px;
        }}
        pre {{
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }}
        blockquote {{
            border-left: 4px solid #ccc;
            padding-left: 10px;
            margin-left: 20px;
            color: #666;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
        @media print {{
            body {{
                padding: 0;
            }}
        }}
    </style>
</head>
<body>
    {html}
</body>
</html>
"""
    
    return html_document