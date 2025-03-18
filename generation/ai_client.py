"""
Módulo cliente para APIs de IA que genera contenido para el informe ambiental.

Este módulo contiene clases y funciones para interactuar con APIs de IA (OpenAI/Anthropic)
y generar contenido coherente para cada sección del informe a partir de segmentos relevantes.
"""

import os
import json
import time
import logging
import requests
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union

# Importar configuración desde el módulo centralizado
from config import (
    OPENAI_API_KEY, 
    ANTHROPIC_API_KEY, 
    OPENAI_MODEL, 
    ANTHROPIC_MODEL,
    TOP_N_SECTIONS,
    SIMILARITY_THRESHOLD
)

# Configuración de logging
logger = logging.getLogger(__name__)


class AIClient(ABC):
    """Clase base abstracta para clientes de APIs de IA."""
    
    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        """
        Genera texto a partir de un prompt usando la API correspondiente.
        
        Args:
            prompt (str): Instrucción o contexto para la generación.
            
        Returns:
            str: Texto generado.
        """
        pass
    
    @abstractmethod
    def get_api_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre la API utilizada.
        
        Returns:
            dict: Información de la API.
        """
        pass


class OpenAIClient(AIClient):
    """Cliente para la API de OpenAI."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Inicializa el cliente de OpenAI.
        
        Args:
            api_key (str, optional): API key para OpenAI. Si no se proporciona,
                                    se usa la variable de entorno OPENAI_API_KEY.
            model (str, optional): Modelo de OpenAI a utilizar. Si no se proporciona,
                                   se usa la configuración de OPENAI_MODEL.
        """
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("Se requiere una API key de OpenAI. Configúrala en el archivo .env")
        
        self.model = model or OPENAI_MODEL
        self.api_base = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        logger.info(f"Cliente OpenAI inicializado con modelo: {self.model}")
    
    def generate_text(self, prompt: str) -> str:
        """
        Genera texto usando la API de OpenAI.
        
        Args:
            prompt (str): Instrucción o contexto para la generación.
            
        Returns:
            str: Texto generado.
            
        Raises:
            Exception: Si hay un error en la llamada a la API.
        """
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5,
            "max_tokens": 2000
        }
        
        try:
            logger.debug(f"Enviando solicitud a OpenAI (longitud prompt: {len(prompt)} caracteres)")
            response = requests.post(
                self.api_base,
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            
            response_data = response.json()
            logger.debug("Respuesta recibida correctamente de OpenAI")
            return response_data["choices"][0]["message"]["content"].strip()
        
        except Exception as e:
            logger.error(f"Error en la llamada a la API de OpenAI: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Detalles: {e.response.text}")
            raise
    
    def get_api_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre la API de OpenAI utilizada.
        
        Returns:
            dict: Información de la API.
        """
        return {
            "provider": "OpenAI",
            "model": self.model,
            "api_version": "v1"
        }


class AnthropicClient(AIClient):
    """Cliente para la API de Anthropic (Claude)."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Inicializa el cliente de Anthropic.
        
        Args:
            api_key (str, optional): API key para Anthropic. Si no se proporciona,
                                    se usa la variable de entorno ANTHROPIC_API_KEY.
            model (str, optional): Modelo de Anthropic a utilizar. Si no se proporciona,
                                   se usa la configuración de ANTHROPIC_MODEL.
        """
        self.api_key = api_key or ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("Se requiere una API key de Anthropic. Configúrala en el archivo .env")
        
        self.model = model or ANTHROPIC_MODEL
        self.api_base = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
            "x-api-key": self.api_key
        }
        logger.info(f"Cliente Anthropic inicializado con modelo: {self.model}")
    
    def generate_text(self, prompt: str) -> str:
        """
        Genera texto usando la API de Anthropic.
        
        Args:
            prompt (str): Instrucción o contexto para la generación.
            
        Returns:
            str: Texto generado.
            
        Raises:
            Exception: Si hay un error en la llamada a la API.
        """
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5,
            "max_tokens": 4000
        }
        
        try:
            logger.debug(f"Enviando solicitud a Anthropic (longitud prompt: {len(prompt)} caracteres)")
            response = requests.post(
                self.api_base,
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            
            response_data = response.json()
            logger.debug("Respuesta recibida correctamente de Anthropic")
            return response_data["content"][0]["text"].strip()
        
        except Exception as e:
            logger.error(f"Error en la llamada a la API de Anthropic: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Detalles: {e.response.text}")
            raise
    
    def get_api_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre la API de Anthropic utilizada.
        
        Returns:
            dict: Información de la API.
        """
        return {
            "provider": "Anthropic",
            "model": self.model,
            "api_version": "2023-06-01"
        }


def create_section_prompt(section: Dict[str, Any], segments: List[Dict[str, Any]]) -> str:
    """
    Crea un prompt para la generación de contenido de una sección.
    
    Args:
        section (dict): Información de la sección.
        segments (list): Lista de segmentos relevantes para la sección.
        
    Returns:
        str: Prompt para la API de IA.
    """
    # Información básica de la sección
    section_info = f"""
# Información de la sección
- Título: {section['titulo']}
- ID: {section['id']}
- Nivel: {section['nivel']}
- Ruta: {section['path']}
"""
    
    if 'descripcion' in section and section['descripcion']:
        section_info += f"- Descripción: {section['descripcion']}\n"
    
    if 'palabras_clave' in section and section['palabras_clave']:
        section_info += f"- Palabras clave: {', '.join(section['palabras_clave'])}\n"
    
    # Extraer y formatear el contenido de los segmentos
    segments_text = ""
    if segments:
        segments_text = "# Segmentos relevantes encontrados en las transcripciones\n\n"
        
        # Ordenar segmentos por score de similitud (de mayor a menor)
        sorted_segments = sorted(segments, key=lambda x: x.get('similarity_score', 0), reverse=True)
        
        for i, segment in enumerate(sorted_segments):
            # Truncar texto muy largo para el prompt
            text = segment['text']
            if len(text) > 1000:  # Limitar segmentos muy largos
                text = text[:1000] + "... [truncado]"
            
            segments_text += f"## Segmento {i+1}\n"
            if 'timestamp' in segment:
                segments_text += f"Timestamp: {segment['timestamp'].get('start', '')} - {segment['timestamp'].get('end', '')}\n"
            segments_text += f"Texto: {text}\n\n"
    else:
        segments_text = "# No se encontraron segmentos relevantes en las transcripciones para esta sección.\n"
    
    # Crear el prompt completo
    prompt = f"""
Eres un especialista en análisis ambiental creando un informe técnico de "Línea Base" a partir de transcripciones de entrevistas.

{section_info}

{segments_text}

# Instrucciones
1. Genera contenido técnico para la sección "{section['titulo']}" basado en los segmentos proporcionados.
2. El contenido debe seguir un formato académico y técnico adecuado para un informe ambiental.
3. Extrae y sintetiza la información relevante de los segmentos.
4. Si no hay información suficiente, indica claramente qué datos serían necesarios completar.
5. Si los segmentos no contienen información relevante para esta sección, genera una nota indicando que no se encontró información aplicable.
6. Incluye, cuando sea posible, datos cuantitativos y cualitativos mencionados en los segmentos.
7. El formato debe ser en Markdown.
8. La extensión debe ser adecuada para la cantidad de información disponible.

# Resultado esperado
Genera el contenido para la sección "{section['titulo']}" siguiendo las instrucciones anteriores:

"""
    
    return prompt


def generate_section_content(section: Dict[str, Any], segments: List[Dict[str, Any]], client: AIClient) -> Dict[str, Any]:
    """
    Genera contenido para una sección usando IA.
    
    Args:
        section (dict): Información de la sección.
        segments (list): Lista de segmentos relevantes para la sección.
        client (AIClient): Cliente de API de IA.
        
    Returns:
        dict: Sección con contenido generado.
    """
    logger.info(f"Generando contenido para sección: {section['titulo']}")
    
    # Crear prompt para la IA
    prompt = create_section_prompt(section, segments)
    
    # Llamar a la API de IA
    try:
        start_time = time.time()
        content = client.generate_text(prompt)
        end_time = time.time()
        
        # Crear resultado
        result = section.copy()
        result['contenido_generado'] = content
        result['metadatos_generacion'] = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'tiempo_ejecucion': round(end_time - start_time, 2),
            'api_info': client.get_api_info(),
            'num_segmentos_usados': len(segments)
        }
        
        logger.info(f"✓ Contenido generado ({result['metadatos_generacion']['tiempo_ejecucion']}s)")
        return result
    
    except Exception as e:
        logger.error(f"✗ Error al generar contenido: {e}")
        # Crear resultado con error
        result = section.copy()
        result['contenido_generado'] = f"**ERROR**: No se pudo generar contenido para esta sección debido a: {str(e)}"
        result['metadatos_generacion'] = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'error': str(e),
            'api_info': client.get_api_info(),
            'num_segmentos_usados': len(segments)
        }
        return result


def process_all_sections(assignments: Dict[str, List[Dict[str, Any]]], 
                        sections: List[Dict[str, Any]], 
                        structure: Dict[str, Any],
                        client_type: str = "openai") -> Dict[str, Any]:
    """
    Procesa todas las secciones y genera contenido para cada una.
    
    Args:
        assignments (dict): Diccionario de asignaciones {section_id: [segments]}.
        sections (list): Lista de secciones.
        structure (dict): Estructura completa del informe.
        client_type (str): Tipo de cliente a usar ('openai' o 'anthropic').
        
    Returns:
        dict: Estructura con contenido generado.
    """
    # Crear cliente de IA según el tipo especificado
    if client_type.lower() == "anthropic":
        try:
            client = AnthropicClient()
            logger.info("Usando Anthropic (Claude) para generación de contenido")
        except Exception as e:
            logger.error(f"Error al inicializar cliente de Anthropic: {e}")
            logger.info("Fallback a OpenAI")
            client = OpenAIClient()
    else:
        try:
            client = OpenAIClient()
            logger.info("Usando OpenAI para generación de contenido")
        except Exception as e:
            logger.error(f"Error al inicializar cliente de OpenAI: {e}")
            try:
                logger.info("Intentando con Anthropic")
                client = AnthropicClient()
            except:
                raise ValueError("No se pudo inicializar ningún cliente de IA. Verifica las claves API en el archivo .env")
    
    # Convertir lista de secciones a diccionario para facilitar acceso
    sections_dict = {section['id']: section for section in sections}
    
    # Crear estructura para resultado
    result_structure = structure.copy()
    result_structure['secciones_generadas'] = {}
    
    # Generar contenido para cada sección
    for section_id, segment_list in assignments.items():
        if section_id in sections_dict:
            section = sections_dict[section_id]
            result = generate_section_content(section, segment_list, client)
            result_structure['secciones_generadas'][section_id] = result
    
    return result_structure


def process_content_for_report(assignments_path: str, structure_path: str, output_path: str = None, client_type: str = "openai") -> Dict[str, Any]:
    """
    Función principal para procesar contenido para el informe.
    
    Args:
        assignments_path (str): Ruta al archivo JSON con asignaciones.
        structure_path (str): Ruta al archivo JSON con la estructura.
        output_path (str, optional): Ruta para guardar el contenido generado.
        client_type (str): Tipo de cliente a usar ('openai' o 'anthropic').
        
    Returns:
        dict: Estructura con contenido generado.
    """
    # Cargar asignaciones y estructura
    try:
        with open(assignments_path, 'r', encoding='utf-8') as file:
            assignments = json.load(file)
        
        with open(structure_path, 'r', encoding='utf-8') as file:
            structure = json.load(file)
        
        # Extraer secciones
        from analysis.vectorizer import extract_sections_data
        sections = extract_sections_data(structure)
        
        logger.info(f"Datos cargados: {len(assignments)} secciones con asignaciones")
    except Exception as e:
        logger.error(f"Error al cargar datos: {e}")
        return {}
    
    # Procesar secciones
    result = process_all_sections(assignments, sections, structure, client_type)
    
    # Guardar resultado si se especificó ruta
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(result, file, ensure_ascii=False, indent=2)
        logger.info(f"Contenido generado guardado en {output_path}")
    
    return result


if __name__ == "__main__":
    # Configuración de logging para ejecución como script
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ejemplo de uso
    import sys
    
    if len(sys.argv) > 2:
        assignments_file = sys.argv[1]
        structure_file = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) > 3 else "generated_content.json"
        client_type = sys.argv[4] if len(sys.argv) > 4 else "openai"
        
        process_content_for_report(assignments_file, structure_file, output_file, client_type)
    else:
        print("Uso: python ai_client.py <archivo_asignaciones> <archivo_estructura> [archivo_salida] [tipo_cliente]")