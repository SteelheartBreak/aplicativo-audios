#!/usr/bin/env python
"""
Script principal para ejecutar el proceso completo de generación de informes.

Este script coordina todas las etapas del proceso, desde la limpieza de transcripciones
hasta la generación del informe final.
"""

import os
import argparse
import json
import time
import logging
import glob
from datetime import datetime

# Importar configuración del módulo centralizado
from config import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_FORMATS,
    validate_config
)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_directory(dir_path):
    """Crea un directorio si no existe."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        logger.info(f"Directorio creado: {dir_path}")


def main():
    """Función principal que coordina todo el proceso."""
    # Validar configuración inicial
    if not validate_config():
        logger.error("La configuración no es válida. Revisa el archivo .env")
        return 1
    
    # Configurar el parser de argumentos
    parser = argparse.ArgumentParser(
        description="Generador automático de informes a partir de transcripciones"
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
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directorio de salida (por defecto: {DEFAULT_OUTPUT_DIR})"
    )
    
    parser.add_argument(
        "-f", "--formats",
        default=",".join(DEFAULT_FORMATS),
        help=f"Formatos de salida separados por comas (por defecto: {','.join(DEFAULT_FORMATS)})"
    )
    
    parser.add_argument(
        "-c", "--client",
        default="openai",
        choices=["openai", "anthropic"],
        help="Cliente de IA a utilizar (por defecto: openai)"
    )
    
    parser.add_argument(
        "--skip-preprocessing",
        action="store_true",
        help="Omitir paso de preprocesamiento (usar archivos existentes)"
    )
    
    parser.add_argument(
        "--skip-analysis",
        action="store_true",
        help="Omitir paso de análisis (usar asignaciones existentes)"
    )
    
    parser.add_argument(
        "--skip-generation",
        action="store_true",
        help="Omitir paso de generación (usar contenido existente)"
    )
    
    # Parsear argumentos
    args = parser.parse_args()
    
    # Crear directorio de salida
    create_directory(args.output)
    
    # Definir rutas de archivos intermedios y finales
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cleaned_file = os.path.join(args.output, f"cleaned_{timestamp}.json")
    segments_file = os.path.join(args.output, f"segments_{timestamp}.json")
    assignments_file = os.path.join(args.output, f"assignments_{timestamp}.json")
    content_file = os.path.join(args.output, f"content_{timestamp}.json")
    report_base = os.path.join(args.output, f"informe_{timestamp}")
    
    formats = [f.strip() for f in args.formats.split(",")]
    
    # Mostrar información inicial
    logger.info("\n==== GENERADOR AUTOMÁTICO DE INFORMES AMBIENTALES ====")
    logger.info(f"Hora de inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Archivo de transcripción: {args.transcription}")
    logger.info(f"Archivo de estructura: {args.structure}")
    logger.info(f"Directorio de salida: {args.output}")
    logger.info(f"Formatos de salida: {', '.join(formats)}")
    logger.info(f"Cliente de IA: {args.client}")
    logger.info("=" * 50 + "\n")
    
    # Registrar tiempo de inicio global
    start_time_global = time.time()
    
    # PASO 1: Preprocesamiento
    if not args.skip_preprocessing:
        logger.info("\n--- ETAPA 1: PREPROCESAMIENTO ---")
        start_time = time.time()
        
        try:
            # Importar módulos de preprocesamiento
            from preprocessing.cleaner import clean_transcription
            from preprocessing.segmenter import process_transcription_for_analysis
            
            # Limpiar transcripción
            logger.info("Limpiando transcripción...")
            clean_segments = clean_transcription(args.transcription, cleaned_file)
            
            # Procesar para análisis
            logger.info("Segmentando transcripción...")
            segments = process_transcription_for_analysis(
                args.transcription, segments_file, cleaned_file
            )
            
            # Mostrar estadísticas
            elapsed_time = time.time() - start_time
            logger.info(f"Preprocesamiento completado en {elapsed_time:.2f} segundos")
            logger.info(f"Segmentos generados: {len(segments)}")
        
        except Exception as e:
            logger.error(f"ERROR en preprocesamiento: {e}")
            return 1
    else:
        logger.info("\n--- ETAPA 1: PREPROCESAMIENTO [OMITIDO] ---")
        # Usar último archivo de segmentos generado
        segments_glob = os.path.join(args.output, "segments_*.json")
        matching_files = sorted(glob.glob(segments_glob), key=os.path.getmtime, reverse=True)
        
        if matching_files:
            segments_file = matching_files[0]
            logger.info(f"Usando archivo de segmentos existente: {segments_file}")
        else:
            logger.error("No se encontraron archivos de segmentos existentes.")
            return 1
    
    # PASO 2: Análisis y clasificación
    if not args.skip_analysis:
        logger.info("\n--- ETAPA 2: ANÁLISIS Y CLASIFICACIÓN ---")
        start_time = time.time()
        
        try:
            # Importar módulo de análisis
            from analysis.vectorizer import process_segments_and_sections
            
            # Procesar segmentos y secciones
            logger.info("Vectorizando y asignando segmentos a secciones...")
            assignments = process_segments_and_sections(
                segments_file, args.structure, assignments_file
            )
            
            # Mostrar estadísticas
            elapsed_time = time.time() - start_time
            logger.info(f"Análisis completado en {elapsed_time:.2f} segundos")
            
            # Contar asignaciones
            total_assignments = sum(len(segments) for segments in assignments.values())
            sections_with_content = sum(1 for segments in assignments.values() if segments)
            
            logger.info(f"Total de asignaciones: {total_assignments}")
            logger.info(f"Secciones con contenido: {sections_with_content}")
        
        except Exception as e:
            logger.error(f"ERROR en análisis: {e}")
            return 1
    else:
        logger.info("\n--- ETAPA 2: ANÁLISIS Y CLASIFICACIÓN [OMITIDO] ---")
        # Usar último archivo de asignaciones generado
        assignments_glob = os.path.join(args.output, "assignments_*.json")
        matching_files = sorted(glob.glob(assignments_glob), key=os.path.getmtime, reverse=True)
        
        if matching_files:
            assignments_file = matching_files[0]
            logger.info(f"Usando archivo de asignaciones existente: {assignments_file}")
        else:
            logger.error("No se encontraron archivos de asignaciones existentes.")
            return 1
    
    # PASO 3: Generación de contenido
    if not args.skip_generation:
        logger.info("\n--- ETAPA 3: GENERACIÓN DE CONTENIDO ---")
        start_time = time.time()
        
        try:
            # Importar módulo de generación
            from generation.ai_client import process_content_for_report
            
            # Generar contenido
            logger.info(f"Generando contenido con {args.client}...")
            content = process_content_for_report(
                assignments_file, args.structure, content_file, args.client
            )
            
            # Mostrar estadísticas
            elapsed_time = time.time() - start_time
            logger.info(f"Generación completada en {elapsed_time:.2f} segundos")
            
            # Contar secciones generadas
            sections_generated = len(content.get('secciones_generadas', {}))
            logger.info(f"Secciones generadas: {sections_generated}")
        
        except Exception as e:
            logger.error(f"ERROR en generación: {e}")
            return 1
    else:
        logger.info("\n--- ETAPA 3: GENERACIÓN DE CONTENIDO [OMITIDO] ---")
        # Usar último archivo de contenido generado
        content_glob = os.path.join(args.output, "content_*.json")
        matching_files = sorted(glob.glob(content_glob), key=os.path.getmtime, reverse=True)
        
        if matching_files:
            content_file = matching_files[0]
            logger.info(f"Usando archivo de contenido existente: {content_file}")
        else:
            logger.error("No se encontraron archivos de contenido existentes.")
            return 1
    
    # PASO 4: Construcción del informe final
    logger.info("\n--- ETAPA 4: CONSTRUCCIÓN DEL INFORME ---")
    start_time = time.time()
    
    try:
        # Importar módulo de construcción
        from generation.content_builder import build_report
        
        # Construir informe
        logger.info(f"Generando informe en formatos: {', '.join(formats)}...")
        generated_files = build_report(
            content_file, args.structure, report_base, formats
        )
        
        # Mostrar estadísticas
        elapsed_time = time.time() - start_time
        logger.info(f"Construcción completada en {elapsed_time:.2f} segundos")
        
        # Listar archivos generados
        logger.info("\nARCHIVOS GENERADOS:")
        for fmt, file_path in generated_files.items():
            logger.info(f"- {fmt.upper()}: {file_path}")
    
    except Exception as e:
        logger.error(f"ERROR en construcción: {e}")
        return 1
    
    # Mostrar tiempo total
    elapsed_time_global = time.time() - start_time_global
    logger.info(f"\nProceso completado en {elapsed_time_global:.2f} segundos")
    
    return 0


if __name__ == "__main__":
    exit(main())