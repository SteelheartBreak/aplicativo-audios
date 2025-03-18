"""
Módulo de segmentación de transcripciones para el generador de informes ambientales.

Este módulo contiene funciones para segmentar las transcripciones limpias
en unidades temáticas que puedan ser analizadas y clasificadas.
"""

import re
import os
import json
import nltk
from nltk.tokenize import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Asegurar que los recursos de NLTK estén descargados
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


def segment_by_sentences(text):
    """
    Segmenta un texto en oraciones.
    
    Args:
        text (str): Texto a segmentar.
        
    Returns:
        list: Lista de oraciones.
    """
    # Consideraciones especiales para español
    # Reemplazar abreviaciones comunes para evitar falsos positivos
    abbreviations = {
        'Dr.': 'Dr',
        'Sr.': 'Sr',
        'Sra.': 'Sra',
        'Srta.': 'Srta',
        'vs.': 'vs',
        'etc.': 'etc',
        'aprox.': 'aprox',
        # Añadir más abreviaciones según sea necesario
    }
    
    for abbr, repl in abbreviations.items():
        text = text.replace(abbr, repl)
    
    # Segmentar en oraciones
    sentences = sent_tokenize(text, language='spanish')
    
    # Restaurar abreviaciones
    for abbr, repl in abbreviations.items():
        sentences = [s.replace(repl, abbr) for s in sentences]
    
    return sentences


def segment_by_topics(segments, threshold=0.3, min_segment_length=50):
    """
    Identifica cambios de tema en los segmentos de texto mediante análisis de similitud.
    
    Args:
        segments (list): Lista de diccionarios con los segmentos de texto.
        threshold (float): Umbral de similitud para considerar cambio de tema (0-1).
        min_segment_length (int): Longitud mínima en caracteres para considerar un segmento válido.
        
    Returns:
        list: Lista de segmentos agrupados por tema.
    """
    # Extraer solo el texto de los segmentos
    texts = [segment['text'] for segment in segments]
    
    # Filtrar segmentos muy cortos
    valid_indices = [i for i, text in enumerate(texts) if len(text) >= min_segment_length]
    valid_texts = [texts[i] for i in valid_indices]
    
    if not valid_texts:
        return []
    
    # Vectorizar textos
    vectorizer = TfidfVectorizer(stop_words='spanish', ngram_range=(1, 2), min_df=1)
    try:
        tfidf_matrix = vectorizer.fit_transform(valid_texts)
    except ValueError:
        # Si hay problemas con la vectorización, retornar segmentos originales
        return [segments[i] for i in valid_indices]
    
    # Matriz de similitud coseno entre segmentos consecutivos
    similarities = []
    for i in range(len(valid_texts) - 1):
        similarity = cosine_similarity(
            tfidf_matrix[i:i+1], 
            tfidf_matrix[i+1:i+2]
        )[0][0]
        similarities.append(similarity)
    
    # Identificar cambios de tema donde la similitud es menor al umbral
    topic_changes = [0]  # Primer segmento siempre inicia un tema
    for i, similarity in enumerate(similarities):
        if similarity < threshold:
            topic_changes.append(i + 1)
    
    # Agrupar segmentos por tema
    topic_segments = []
    for i in range(len(topic_changes)):
        start_idx = valid_indices[topic_changes[i]]
        
        # Determinar el índice final para este tema
        if i < len(topic_changes) - 1:
            end_idx = valid_indices[topic_changes[i+1] - 1] + 1
        else:
            end_idx = len(segments)
        
        # Crear un nuevo segmento agrupado
        combined_text = " ".join(texts[start_idx:end_idx])
        combined_timestamp = {
            'start': segments[start_idx]['timestamp']['start'],
            'end': segments[end_idx - 1]['timestamp']['end']
        }
        
        topic_segments.append({
            'timestamp': combined_timestamp,
            'text': combined_text,
            'original_indices': list(range(start_idx, end_idx))
        })
    
    return topic_segments


def create_text_chunks(text, max_chunk_size=1000, overlap=100):
    """
    Divide textos largos en trozos más pequeños para procesamiento con IA.
    
    Args:
        text (str): Texto a dividir.
        max_chunk_size (int): Tamaño máximo en caracteres de cada trozo.
        overlap (int): Número de caracteres de superposición entre trozos.
        
    Returns:
        list: Lista de trozos de texto.
    """
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Determinar el final de este trozo
        end = min(start + max_chunk_size, len(text))
        
        # Si no estamos al final del texto, buscar un buen punto de corte
        if end < len(text):
            # Buscar el último punto o marca de párrafo
            last_period = text.rfind('.', start, end)
            last_newline = text.rfind('\n', start, end)
            
            # Elegir el punto de corte más adecuado
            if last_period > start + (max_chunk_size // 2):
                end = last_period + 1  # Incluir el punto
            elif last_newline > start + (max_chunk_size // 2):
                end = last_newline + 1  # Incluir el salto de línea
        
        # Añadir el trozo
        chunks.append(text[start:end])
        
        # Calcular el inicio del siguiente trozo considerando la superposición
        start = max(0, end - overlap)
    
    return chunks


def process_transcription_for_analysis(file_path, output_path=None, clean_output_path=None):
    """
    Función principal que procesa una transcripción para su análisis.
    
    Args:
        file_path (str): Ruta al archivo de transcripción.
        output_path (str, optional): Ruta para guardar los segmentos procesados.
        clean_output_path (str, optional): Ruta para guardar la transcripción limpia.
        
    Returns:
        list: Lista de segmentos procesados listos para análisis.
    """
    # Importar el módulo de limpieza
    from preprocessing.cleaner import clean_transcription
    
    # 1. Limpiar la transcripción
    clean_segments = clean_transcription(file_path, clean_output_path)
    if not clean_segments:
        print("No se pudieron obtener segmentos limpios.")
        return []
    
    # 2. Segmentar por temas
    topic_segments = segment_by_topics(clean_segments)
    print(f"Se identificaron {len(topic_segments)} segmentos temáticos")
    
    # 3. Para cada segmento temático, dividir en trozos si es necesario
    analysis_segments = []
    for segment in topic_segments:
        # Dividir texto en trozos más pequeños si es muy largo
        text_chunks = create_text_chunks(segment['text'])
        
        # Si solo hay un trozo, mantener el segmento original
        if len(text_chunks) == 1:
            analysis_segments.append(segment)
        else:
            # Crear nuevos segmentos para cada trozo
            for i, chunk in enumerate(text_chunks):
                new_segment = {
                    'timestamp': segment['timestamp'],
                    'text': chunk,
                    'original_indices': segment['original_indices'],
                    'chunk_index': i,
                    'total_chunks': len(text_chunks)
                }
                analysis_segments.append(new_segment)
    
    print(f"Total de segmentos para análisis: {len(analysis_segments)}")
    
    # Guardar resultado si se especificó una ruta de salida
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(analysis_segments, file, ensure_ascii=False, indent=2)
        print(f"Segmentos procesados guardados en {output_path}")
    
    return analysis_segments


if __name__ == "__main__":
    # Ejemplo de uso
    import sys
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "processed_segments.json"
        clean_file = sys.argv[3] if len(sys.argv) > 3 else "cleaned_transcription.json"
        process_transcription_for_analysis(input_file, output_file, clean_file)
    else:
        print("Uso: python segmenter.py <archivo_transcripcion> [archivo_salida] [archivo_limpio]")