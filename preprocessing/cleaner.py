"""
Módulo de limpieza de transcripciones para el generador de informes ambientales.

Este módulo contiene funciones para cargar, limpiar y preprocesar las transcripciones
de audio antes de su procesamiento para clasificación y generación de contenido.
"""

import re
import os
import json


def load_transcription(file_path):
    """
    Carga un archivo de transcripción.
    
    Args:
        file_path (str): Ruta al archivo de transcripción.
        
    Returns:
        str: Contenido del archivo de transcripción.
        
    Raises:
        FileNotFoundError: Si el archivo no existe.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"El archivo de transcripción {file_path} no existe.")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        transcription = file.read()
    
    return transcription


def extract_timestamped_segments(transcription):
    """
    Extrae segmentos con marcas temporales de una transcripción.
    
    Args:
        transcription (str): Contenido de la transcripción.
        
    Returns:
        list: Lista de diccionarios con los segmentos y sus marcas temporales.
              Cada diccionario tiene las claves 'timestamp' y 'text'.
    """
    # Patrón para buscar: [HH:MM:SS - HH:MM:SS]: texto
    pattern = r'\[(\d{2}:\d{2}:\d{2}) - (\d{2}:\d{2}:\d{2})\]:(.*?)(?=\n\[|$)'
    matches = re.findall(pattern, transcription, re.DOTALL)
    
    segments = []
    for start_time, end_time, text in matches:
        segments.append({
            'timestamp': {
                'start': start_time,
                'end': end_time
            },
            'text': text.strip()
        })
    
    return segments


def correct_common_transcription_errors(text):
    """
    Corrige errores comunes en las transcripciones.
    
    Args:
        text (str): Texto a corregir.
        
    Returns:
        str: Texto corregido.
    """
    # Corregir errores comunes de transcripción automática
    corrections = {
        # Errores típicos de nombres propios y términos técnicos
        'comfama': 'Comfama',
        'san luis': 'San Luis',
        'bosquecinos': 'Bosquecinos',
        'cubas': 'Cuba',
        'pantagoras': 'Pantagoras',
        'arnulfo': 'Arnulfo',
        'ndvi': 'NDVI',
        
        # Errores de puntuación
        ',,': ',',
        '..': '.',
        ' ,': ',',
        ' .': '.',
        
        # Errores de espaciado
        '  ': ' ',
        
        # Términos mal transcritos comunes
        'eh': '',
        'este': '',
        'pues': '',
        'cierto': '',
        'digamos': '',
    }
    
    # Aplicar correcciones
    for error, correction in corrections.items():
        text = re.sub(r'\\b' + error + r'\\b', correction, text, flags=re.IGNORECASE)
    
    return text


def normalize_punctuation(text):
    """
    Normaliza la puntuación en el texto.
    
    Args:
        text (str): Texto a normalizar.
        
    Returns:
        str: Texto con puntuación normalizada.
    """
    # Eliminar espacios antes de signos de puntuación
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    
    # Asegurar que haya un espacio después de los signos de puntuación
    text = re.sub(r'([.,;:!?])([^\s])', r'\1 \2', text)
    
    # Normalizar puntos suspensivos
    text = re.sub(r'\.{2,}', '...', text)
    
    # Asegurar que los paréntesis tengan el espaciado correcto
    text = re.sub(r'\(\s+', '(', text)
    text = re.sub(r'\s+\)', ')', text)
    
    # Eliminar múltiples espacios consecutivos
    text = re.sub(r'\s{2,}', ' ', text)
    
    return text.strip()


def clean_speaker_indicators(text):
    """
    Elimina indicadores de hablantes del texto (ej: "Juan:", "Persona 1:").
    
    Args:
        text (str): Texto a limpiar.
        
    Returns:
        str: Texto sin indicadores de hablantes.
    """
    # Patrón para identificar indicadores de hablante al inicio de línea o después de punto
    pattern = r'(^|\. )([A-Za-zÁÉÍÓÚáéíóúÑñ]+ ?[A-Za-zÁÉÍÓÚáéíóúÑñ]*:)\s+'
    
    # Eliminar indicadores de hablante
    text = re.sub(pattern, r'\1', text)
    
    return text


def merge_related_segments(segments, max_gap_seconds=30):
    """
    Fusiona segmentos relacionados basado en proximidad temporal y temática.
    
    Args:
        segments (list): Lista de diccionarios con segmentos y marcas temporales.
        max_gap_seconds (int): Tiempo máximo en segundos para considerar segmentos contiguos.
        
    Returns:
        list: Lista de segmentos fusionados.
    """
    if not segments:
        return []
    
    # Función auxiliar para convertir tiempo (HH:MM:SS) a segundos
    def time_to_seconds(time_str):
        h, m, s = map(int, time_str.split(':'))
        return h * 3600 + m * 60 + s
    
    merged_segments = []
    current_segment = segments[0].copy()
    
    for i in range(1, len(segments)):
        prev_end_time = time_to_seconds(current_segment['timestamp']['end'])
        current_start_time = time_to_seconds(segments[i]['timestamp']['start'])
        
        # Si la brecha temporal es pequeña, fusionar
        if current_start_time - prev_end_time <= max_gap_seconds:
            # Actualizar el tiempo final
            current_segment['timestamp']['end'] = segments[i]['timestamp']['end']
            # Concatenar el texto
            current_segment['text'] += " " + segments[i]['text']
        else:
            # Guardar el segmento actual y comenzar uno nuevo
            merged_segments.append(current_segment)
            current_segment = segments[i].copy()
    
    # Añadir el último segmento
    merged_segments.append(current_segment)
    
    return merged_segments


def clean_transcription(file_path, output_path=None):
    """
    Función principal que aplica todo el pipeline de limpieza a una transcripción.
    
    Args:
        file_path (str): Ruta al archivo de transcripción.
        output_path (str, optional): Ruta para guardar la transcripción limpia.
                                    Si es None, no guarda archivo.
        
    Returns:
        list: Lista de segmentos limpios.
    """
    # Cargar transcripción
    try:
        transcription = load_transcription(file_path)
        print(f"Transcripción cargada correctamente desde {file_path}")
    except Exception as e:
        print(f"Error al cargar la transcripción: {e}")
        return []
    
    # Extraer segmentos con marcas temporales
    segments = extract_timestamped_segments(transcription)
    print(f"Se extrajeron {len(segments)} segmentos con marcas temporales")
    
    # Limpiar y corregir cada segmento
    for segment in segments:
        # Corrección de errores comunes
        segment['text'] = correct_common_transcription_errors(segment['text'])
        
        # Normalización de puntuación
        segment['text'] = normalize_punctuation(segment['text'])
        
        # Limpieza de indicadores de hablantes
        segment['text'] = clean_speaker_indicators(segment['text'])
    
    # Fusionar segmentos relacionados
    merged_segments = merge_related_segments(segments)
    print(f"Después de fusionar, quedan {len(merged_segments)} segmentos")
    
    # Guardar resultado si se especificó una ruta de salida
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(merged_segments, file, ensure_ascii=False, indent=2)
        print(f"Transcripción limpia guardada en {output_path}")
    
    return merged_segments


if __name__ == "__main__":
    # Ejemplo de uso
    import sys
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "cleaned_transcription.json"
        clean_transcription(input_file, output_file)
    else:
        print("Uso: python cleaner.py <archivo_transcripcion> [archivo_salida]")