"""
Módulo de vectorización y clasificación de segmentos para el generador de informes ambientales.

Este módulo contiene funciones para vectorizar segmentos de texto y secciones de informes,
calcular similitudes y asignar segmentos a las secciones más relevantes.
"""

import os
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Intentar importar transformers para embeddings más avanzados
try:
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Advertencia: sentence-transformers no está instalado. Se usará TF-IDF en su lugar.")
    print("Para instalar: pip install sentence-transformers")

import os
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Intentar importar transformers para embeddings más avanzados
try:
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Advertencia: sentence-transformers no está instalado. Se usará TF-IDF en su lugar.")
    print("Para instalar: pip install sentence-transformers")


def load_report_structure(structure_path):
    """
    Carga la estructura del informe desde un archivo JSON.
    
    Args:
        structure_path (str): Ruta al archivo JSON con la estructura.
        
    Returns:
        dict: Estructura del informe.
        
    Raises:
        FileNotFoundError: Si el archivo no existe.
        json.JSONDecodeError: Si el archivo no es un JSON válido.
    """
    if not os.path.exists(structure_path):
        raise FileNotFoundError(f"El archivo de estructura {structure_path} no existe.")
    
    with open(structure_path, 'r', encoding='utf-8') as file:
        structure = json.load(file)
    
    return structure


def extract_sections_data(structure):
    """
    Extrae datos planos de todas las secciones en la estructura del informe.
    
    Args:
        structure (dict): Estructura del informe.
        
    Returns:
        list: Lista de diccionarios con información de cada sección.
    """
    sections = []
    
    def process_section(section, path=""):
        # Crear un diccionario con la información de esta sección
        current_path = f"{path}/{section['titulo']}" if path else section['titulo']
        
        section_data = {
            'id': section['id'],
            'titulo': section['titulo'],
            'nivel': section['nivel'],
            'path': current_path,
            'palabras_clave': section.get('palabras_clave', []),
            'descripcion': section.get('descripcion', '')
        }
        
        # Crear texto representativo de la sección para vectorización
        texts = [section['titulo']]
        if section_data['descripcion']:
            texts.append(section_data['descripcion'])
        if section_data['palabras_clave']:
            texts.append(' '.join(section_data['palabras_clave']))
        
        section_data['texto_representativo'] = ' '.join(texts)
        
        # Añadir esta sección a la lista
        sections.append(section_data)
        
        # Procesar subsecciones recursivamente
        if 'subsecciones' in section:
            for subsection in section['subsecciones']:
                process_section(subsection, current_path)
    
    # Procesar secciones principales
    for section in structure['secciones']:
        process_section(section)
    
    return sections


def load_embedding_model(model_name='paraphrase-multilingual-MiniLM-L12-v2'):
    """
    Carga un modelo de embeddings preentrenado.
    
    Args:
        model_name (str): Nombre del modelo de SentenceTransformers a cargar.
        
    Returns:
        SentenceTransformer o None: Modelo cargado o None si no está disponible.
    """
    if not TRANSFORMERS_AVAILABLE:
        return None
    
    try:
        model = SentenceTransformer(model_name)
        print(f"Modelo {model_name} cargado correctamente")
        return model
    except Exception as e:
        print(f"Error al cargar el modelo {model_name}: {e}")
        return None


def vectorize_with_transformers(texts, model):
    """
    Vectoriza textos usando un modelo transformer.
    
    Args:
        texts (list): Lista de textos a vectorizar.
        model (SentenceTransformer): Modelo de embeddings.
        
    Returns:
        numpy.ndarray: Matriz de embeddings.
    """
    return model.encode(texts, show_progress_bar=False)


def vectorize_with_tfidf(texts):
    """
    Vectoriza textos usando TF-IDF.
    
    Args:
        texts (list): Lista de textos a vectorizar.
        
    Returns:
        tuple: (vectorizer, matriz TF-IDF).
    """
    vectorizer = TfidfVectorizer(stop_words='spanish', ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(texts)
    return vectorizer, tfidf_matrix


def calculate_similarity_matrix(section_vectors, segment_vectors):
    """
    Calcula matriz de similitud entre secciones y segmentos.
    
    Args:
        section_vectors (numpy.ndarray): Matriz de vectores de secciones.
        segment_vectors (numpy.ndarray): Matriz de vectores de segmentos.
        
    Returns:
        numpy.ndarray: Matriz de similitud (segmentos x secciones).
    """
    # Si son matrices dispersas de TF-IDF
    if hasattr(section_vectors, 'toarray') and hasattr(segment_vectors, 'toarray'):
        return cosine_similarity(segment_vectors, section_vectors)
    
    # Si son matrices densas de embeddings
    return cosine_similarity(segment_vectors, section_vectors)


def assign_segments_to_sections(similarity_matrix, segments, sections, top_n=3, threshold=0.1):
    """
    Asigna segmentos a secciones basado en la matriz de similitud.
    
    Args:
        similarity_matrix (numpy.ndarray): Matriz de similitud (segmentos x secciones).
        segments (list): Lista de segmentos.
        sections (list): Lista de secciones.
        top_n (int): Número máximo de secciones a asignar por segmento.
        threshold (float): Umbral mínimo de similitud para asignar.
        
    Returns:
        dict: Diccionario de asignaciones {section_id: [segments]}.
    """
    assignments = {section['id']: [] for section in sections}
    
    for i, segment in enumerate(segments):
        # Obtener índices de las secciones más relevantes para este segmento
        section_similarities = similarity_matrix[i]
        
        # Filtrar por umbral mínimo
        relevant_indices = np.where(section_similarities >= threshold)[0]
        
        # Ordenar por similitud descendente y tomar los top_n
        top_indices = relevant_indices[np.argsort(-section_similarities[relevant_indices])][:top_n]
        
        # Si no hay secciones relevantes, pasar al siguiente segmento
        if len(top_indices) == 0:
            continue
        
        # Asignar segmento a las secciones más relevantes
        for idx in top_indices:
            section_id = sections[idx]['id']
            
            # Añadir el segmento a la sección con su valor de similitud
            segment_with_score = segment.copy()
            segment_with_score['similarity_score'] = float(section_similarities[idx])
            assignments[section_id].append(segment_with_score)
    
    return assignments


if __name__ == "__main__":
    # Ejemplo de uso
    import sys
    
    if len(sys.argv) > 2:
        segments_file = sys.argv[1]
        structure_file = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) > 3 else "segment_assignments.json"
        process_segments_and_sections(segments_file, structure_file, output_file)
    else:
        print("Uso: python vectorizer.py <archivo_segmentos> <archivo_estructura> [archivo_salida]")


def process_segments_and_sections(segments_path, structure_path, output_path=None):
    """
    Función principal para procesar segmentos y secciones, vectorizarlos y asignar.
    
    Args:
        segments_path (str): Ruta al archivo JSON con los segmentos.
        structure_path (str): Ruta al archivo JSON con la estructura.
        output_path (str, optional): Ruta para guardar las asignaciones.
        
    Returns:
        dict: Diccionario de asignaciones {section_id: [segments]}.
    """
    """
    Función principal para procesar segmentos y secciones, vectorizarlos y asignar.
    
    Args:
        segments_path (str): Ruta al archivo JSON con los segmentos.
        structure_path (str): Ruta al archivo JSON con la estructura.
        output_path (str, optional): Ruta para guardar las asignaciones.
        
    Returns:
        dict: Diccionario de asignaciones {section_id: [segments]}.
    """
    # 1. Cargar datos
    try:
        with open(segments_path, 'r', encoding='utf-8') as file:
            segments = json.load(file)
        
        structure = load_report_structure(structure_path)
        sections = extract_sections_data(structure)
        
        print(f"Cargados {len(segments)} segmentos y {len(sections)} secciones")
    except Exception as e:
        print(f"Error al cargar datos: {e}")
        return {}
    
    # 2. Preparar textos para vectorización
    segment_texts = [segment['text'] for segment in segments]
    section_texts = [section['texto_representativo'] for section in sections]
    
    # 3. Vectorizar textos
    model = None
    if TRANSFORMERS_AVAILABLE:
        model = load_embedding_model()
    
    if model:
        # Usar embeddings de transformer
        print("Usando embeddings de transformer para vectorización")
        segment_vectors = vectorize_with_transformers(segment_texts, model)
        section_vectors = vectorize_with_transformers(section_texts, model)
    else:
        # Usar TF-IDF
        print("Usando TF-IDF para vectorización")
        vectorizer, section_vectors = vectorize_with_tfidf(section_texts)
        _, segment_vectors = vectorize_with_tfidf(segment_texts)  # Reusamos el mismo vectorizer
    
    # 4. Calcular matriz de similitud
    similarity_matrix = calculate_similarity_matrix(section_vectors, segment_vectors)
    print(f"Matriz de similitud calculada: {similarity_matrix.shape}")
    
    # 5. Asignar segmentos a secciones
    assignments = assign_segments_to_sections(
        similarity_matrix, segments, sections, top_n=3, threshold=0.1
    )
    
    # Ordenar segmentos por relevancia dentro de cada sección
    for section_id, section_segments in assignments.items():
        assignments[section_id] = sorted(
            section_segments, 
            key=lambda x: x['similarity_score'], 
            reverse=True
        )
    
    # 6. Guardar asignaciones si se especificó ruta
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(assignments, file, ensure_ascii=False, indent=2)
        print(f"Asignaciones guardadas en {output_path}")
    
    return assignments