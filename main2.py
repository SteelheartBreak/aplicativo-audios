#!/usr/bin/env python
"""
Script principal para la preparación y análisis de transcripciones ambientales.

Este script ilustra detalladamente los pasos de:
1. Limpieza de transcripciones
2. Segmentación y preprocesamiento
3. Análisis y clasificación de contenido según una estructura de informe
4. Visualización de los resultados

El resultado final es una asignación de segmentos de transcripción a
secciones específicas de la estructura del informe.
"""

import os
import sys
import json
import time
import glob
import argparse
from datetime import datetime
from pprint import pprint
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_directory(dir_path):
    """Crea un directorio si no existe."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"✓ Directorio creado: {dir_path}")

def print_section_separator(title):
    """Imprime un separador de sección con título para mejor visualización."""
    separator = "=" * 80
    print(f"\n{separator}")
    print(f"  {title.upper()}")
    print(f"{separator}\n")

def print_step_info(step_title):
    """Imprime información sobre un paso específico del proceso."""
    print(f"\n➤ {step_title}...")

def json_pretty_print(data, limit=3):
    """
    Imprime datos JSON de forma legible con límite en listas/diccionarios.
    
    Args:
        data: Datos a imprimir (dict o list)
        limit: Número máximo de elementos a mostrar para listas/diccionarios
    """
    if isinstance(data, dict):
        print("{")
        items = list(data.items())
        for i, (key, value) in enumerate(items[:limit]):
            if isinstance(value, (dict, list)) and len(value) > limit:
                if isinstance(value, dict):
                    print(f"  '{key}': {{ ... }} ({len(value)} elementos)")
                else:
                    print(f"  '{key}': [ ... ] ({len(value)} elementos)")
            else:
                print(f"  '{key}': {repr(value)}")
        if len(data) > limit:
            print(f"  ... ({len(data) - limit} elementos más)")
        print("}")
    elif isinstance(data, list):
        print("[")
        for i, item in enumerate(data[:limit]):
            if isinstance(item, (dict, list)) and len(item) > limit:
                if isinstance(item, dict):
                    print(f"  {{ ... }} ({len(item)} elementos)")
                else:
                    print(f"  [ ... ] ({len(item)} elementos)")
            else:
                print(f"  {repr(item)}")
        if len(data) > limit:
            print(f"  ... ({len(data) - limit} elementos más)")
        print("]")
    else:
        print(repr(data))

def load_file(file_path, expected_type=None):
    """
    Carga un archivo y verifica su tipo.
    
    Args:
        file_path: Ruta al archivo
        expected_type: Tipo esperado ('json', 'txt', etc.)
        
    Returns:
        El contenido del archivo
    """
    print_step_info(f"Cargando archivo: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"✗ Error: El archivo {file_path} no existe")
        sys.exit(1)
    
    # Determinar tipo de archivo por extensión
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # Verificar tipo esperado
    if expected_type and f".{expected_type}" != file_ext:
        print(f"⚠ Advertencia: Se esperaba un archivo .{expected_type}, pero se recibió {file_ext}")
    
    # Cargar según tipo
    try:
        if file_ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                print(f"✓ Archivo JSON cargado correctamente (tamaño: {len(json.dumps(data))} bytes)")
                return data
        else:  # Texto plano por defecto
            with open(file_path, 'r', encoding='utf-8') as file:
                data = file.read()
                print(f"✓ Archivo de texto cargado correctamente (tamaño: {len(data)} caracteres)")
                return data
    except Exception as e:
        print(f"✗ Error al cargar el archivo: {str(e)}")
        sys.exit(1)

def save_file(data, file_path):
    """
    Guarda datos en un archivo.
    
    Args:
        data: Datos a guardar
        file_path: Ruta donde guardar el archivo
    """
    print_step_info(f"Guardando archivo: {file_path}")
    
    try:
        # Determinar tipo de archivo por extensión
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.json':
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
                print(f"✓ Archivo JSON guardado correctamente")
        else:  # Texto plano por defecto
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(data)
                print(f"✓ Archivo de texto guardado correctamente")
    except Exception as e:
        print(f"✗ Error al guardar el archivo: {str(e)}")
        return None

def main():
    """Función principal que coordina todo el proceso."""
    # Configurar el parser de argumentos
    parser = argparse.ArgumentParser(
        description="Procesamiento y análisis de transcripciones para informes"
    )
    
    parser.add_argument(
        "-t", "--transcription",
        required=True,
        help="Ruta al archivo de transcripción"
    )
    
    parser.add_argument(
        "-s", "--structure",
        required=True,
        help="Ruta al archivo JSON de estructura de informe"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="output",
        help="Directorio de salida (por defecto: output)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Mostrar información detallada del proceso"
    )
    
    # Parsear argumentos
    args = parser.parse_args()
    
    # Ajustar nivel de log según verbosidad
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Crear directorio de salida
    create_directory(args.output)
    
    # Definir rutas de archivos intermedios
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cleaned_file = os.path.join(args.output, f"cleaned_{timestamp}.json")
    segments_file = os.path.join(args.output, f"segments_{timestamp}.json")
    assignments_file = os.path.join(args.output, f"assignments_{timestamp}.json")
    
    # Mostrar información inicial
    print_section_separator("PROCESAMIENTO DE TRANSCRIPCIONES AMBIENTALES")
    print(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Archivo de transcripción: {args.transcription}")
    print(f"Archivo de estructura: {args.structure}")
    print(f"Directorio de salida: {args.output}")
    
    # Registrar tiempo de inicio global
    start_time_global = time.time()
    
    #-------------------------------------------------------------
    # PASO 1: Cargar y examinar estructura del informe
    #-------------------------------------------------------------
    print_section_separator("PASO 1: CARGA Y EXAMEN DE ESTRUCTURA DEL INFORME")
    start_time = time.time()

    # 1.1 Cargar estructura del informe
    print_step_info("Cargando estructura del informe")
    structure = load_file(args.structure, expected_type='json')
    
    # 1.2 Extraer y mostrar información de secciones
    print_step_info("Analizando estructura del informe")
    
    # Importar función para extraer secciones (permite ver la estructura plana)
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from analysis.vectorizer import extract_sections_data
    
    sections = extract_sections_data(structure)
    
    # Mostrar estadísticas de la estructura
    print(f"✓ Estructura cargada: {len(sections)} secciones identificadas")
    print(f"✓ Niveles de sección: {min(s['nivel'] for s in sections)} a {max(s['nivel'] for s in sections)}")
    
    # Mostrar algunas secciones como ejemplo
    print("\nEjemplo de secciones en la estructura:")
    for i, section in enumerate(sections[:3]):
        print(f"\nSección {i+1}:")
        print(f"  ID: {section['id']}")
        print(f"  Título: {section['titulo']}")
        print(f"  Nivel: {section['nivel']}")
        print(f"  Ruta: {section['path']}")
        if 'palabras_clave' in section and section['palabras_clave']:
            print(f"  Palabras clave: {', '.join(section['palabras_clave'])}")
    
    if len(sections) > 3:
        print(f"\n... y {len(sections) - 3} secciones más.")
    
    elapsed_time = time.time() - start_time
    print(f"\n✓ Análisis de estructura completado en {elapsed_time:.2f} segundos")
    
    #-------------------------------------------------------------
    # PASO 2: Preprocesamiento de la transcripción
    #-------------------------------------------------------------
    print_section_separator("PASO 2: PREPROCESAMIENTO DE LA TRANSCRIPCIÓN")
    start_time = time.time()
    
    # 2.1 Cargar transcripción original
    print_step_info("Cargando archivo de transcripción")
    transcription_content = load_file(args.transcription)
    
    # Mostrar fragmento de la transcripción
    lines = transcription_content.split("\n")
    print("\nFragmento de la transcripción original:")
    for line in lines[:5]:
        print(f"  {line}")
    if len(lines) > 5:
        print(f"  ... ({len(lines)} líneas en total)")
    
    # 2.2 Limpiar transcripción
    print_step_info("Limpiando transcripción")
    from preprocessing.cleaner import clean_transcription
    
    clean_segments = clean_transcription(args.transcription, cleaned_file)
    
    # Mostrar ejemplos de segmentos limpios
    print(f"\n✓ Limpieza completada: {len(clean_segments)} segmentos extraídos")
    print("\nEjemplos de segmentos limpios:")
    for i, segment in enumerate(clean_segments[:2]):
        print(f"\nSegmento {i+1}:")
        print(f"  Timestamp: {segment['timestamp']['start']} - {segment['timestamp']['end']}")
        text = segment['text']
        if len(text) > 100:
            text = text[:100] + "..."
        print(f"  Texto: {text}")
    
    # 2.3 Segmentar por temas y preparar para análisis
    print_step_info("Segmentando transcripción por temas")
    from preprocessing.segmenter import process_transcription_for_analysis
    
    analysis_segments = process_transcription_for_analysis(
        args.transcription, segments_file, cleaned_file
    )
    
    # Mostrar ejemplos de segmentos temáticos
    print(f"\n✓ Segmentación completada: {len(analysis_segments)} segmentos para análisis")
    print("\nEjemplos de segmentos preparados para análisis:")
    for i, segment in enumerate(analysis_segments[:2]):
        print(f"\nSegmento de análisis {i+1}:")
        print(f"  Timestamp: {segment['timestamp']['start']} - {segment['timestamp']['end']}")
        text = segment['text']
        if len(text) > 100:
            text = text[:100] + "..."
        print(f"  Texto: {text}")
        if 'original_indices' in segment:
            print(f"  Segmentos originales incluidos: {len(segment['original_indices'])}")
    
    elapsed_time = time.time() - start_time
    print(f"\n✓ Preprocesamiento completado en {elapsed_time:.2f} segundos")

    #-------------------------------------------------------------
    # PASO 3: Vectorización y clasificación
    #-------------------------------------------------------------
    print_section_separator("PASO 3: VECTORIZACIÓN Y CLASIFICACIÓN")
    start_time = time.time()
    
    # 3.1 Vectorizar y clasificar segmentos
    print_step_info("Vectorizando y clasificando segmentos")
    from analysis.vectorizer import process_segments_and_sections
    
    # Procesar segmentos y asignarlos a secciones
    assignments = process_segments_and_sections(
        segments_file, args.structure, assignments_file
    )
    
    # 3.2 Analizar y mostrar resultados de clasificación
    # Contar asignaciones y estadísticas
    total_segments_assigned = sum(len(segments) for segments in assignments.values())
    sections_with_content = sum(1 for segments in assignments.values() if segments)
    empty_sections = sum(1 for segments in assignments.values() if not segments)
    
    print(f"\n✓ Clasificación completada")
    print(f"  Total de segmentos asignados: {total_segments_assigned}")
    print(f"  Secciones con contenido: {sections_with_content}")
    print(f"  Secciones sin contenido: {empty_sections}")
    
    # Mostrar las secciones con más contenido
    print("\nSecciones con más contenido:")
    top_sections = sorted(
        [(section_id, len(segments)) for section_id, segments in assignments.items()],
        key=lambda x: x[1], reverse=True
    )[:5]
    
    for section_id, count in top_sections:
        if count > 0:
            # Buscar el título de la sección
            section_title = next((s['titulo'] for s in sections if s['id'] == section_id), section_id)
            print(f"  • {section_title}: {count} segmentos")
    
    # Guardar asignaciones
    save_file(assignments, assignments_file)
    
    elapsed_time = time.time() - start_time
    print(f"\n✓ Vectorización y clasificación completadas en {elapsed_time:.2f} segundos")
    
    #-------------------------------------------------------------
    # PASO 4: Visualización detallada de una sección (ejemplo)
    #-------------------------------------------------------------
    print_section_separator("PASO 4: VISUALIZACIÓN DETALLADA DE UNA SECCIÓN")
    
    # Seleccionar una sección con contenido para mostrar en detalle
    example_section_id = top_sections[0][0] if top_sections else None
    
    if example_section_id and assignments[example_section_id]:
        # Buscar información de la sección
        section_info = next((s for s in sections if s['id'] == example_section_id), None)
        
        if section_info:
            print(f"Mostrando contenido para la sección: {section_info['titulo']}")
            print(f"ID de sección: {example_section_id}")
            print(f"Nivel: {section_info['nivel']}")
            print(f"Ruta completa: {section_info['path']}")
            if 'descripcion' in section_info and section_info['descripcion']:
                print(f"Descripción: {section_info['descripcion']}")
            if 'palabras_clave' in section_info and section_info['palabras_clave']:
                print(f"Palabras clave: {', '.join(section_info['palabras_clave'])}")
            
            # Mostrar segmentos relevantes
            print(f"\nSegmentos relevantes para esta sección ({len(assignments[example_section_id])}):")
            
            for i, segment in enumerate(assignments[example_section_id][:3]):
                print(f"\nSegmento {i+1}:")
                print(f"  Timestamp: {segment['timestamp']['start']} - {segment['timestamp']['end']}")
                
                # Mostrar score de similitud
                if 'similarity_score' in segment:
                    print(f"  Score de similitud: {segment['similarity_score']:.4f}")
                
                # Mostrar texto (truncado si es largo)
                text = segment['text']
                if len(text) > 150:
                    text = text[:150] + "..."
                print(f"  Texto: {text}")
            
            if len(assignments[example_section_id]) > 3:
                print(f"\n... y {len(assignments[example_section_id]) - 3} segmentos más.")
        else:
            print("No se pudo encontrar información detallada para la sección seleccionada.")
    else:
        print("No hay secciones con contenido para mostrar en detalle.")
    
    #-------------------------------------------------------------
    # RESUMEN FINAL
    #-------------------------------------------------------------
    elapsed_time_global = time.time() - start_time_global
    print_section_separator("RESUMEN DEL PROCESO")
    print(f"Tiempo total del proceso: {elapsed_time_global:.2f} segundos")
    print(f"Segmentos iniciales extraídos: {len(clean_segments)}")
    print(f"Segmentos procesados para análisis: {len(analysis_segments)}")
    print(f"Total de segmentos asignados a secciones: {total_segments_assigned}")
    print(f"Secciones con contenido: {sections_with_content} de {len(sections)}")
    print(f"\nArchivos generados:")
    print(f"  • Segmentos limpios: {cleaned_file}")
    print(f"  • Segmentos para análisis: {segments_file}")
    print(f"  • Asignaciones a secciones: {assignments_file}")
    
    print(f"\n✓ Proceso completado con éxito")
    
    # Instrucciones para pasos siguientes
    print_section_separator("PRÓXIMOS PASOS")
    print("Para continuar con la generación del informe, ejecute main.py con los siguientes argumentos:")
    print(f"\npython main.py -t {args.transcription} -s {args.structure} --skip-preprocessing --skip-analysis -o {args.output}")
    print("\nEsto usará las asignaciones generadas y continuará con el proceso de generación de contenido y construcción del informe.")
    
    return 0

if __name__ == "__main__":
    exit(main())