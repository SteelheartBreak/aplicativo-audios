"""
Módulo de configuración para cargar variables de entorno

Este módulo se encarga de cargar las variables de entorno desde un archivo .env
y proporciona acceso centralizado a los parámetros de configuración.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno desde el archivo .env
env_path = Path(__file__).resolve().parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger.info(f"Variables de entorno cargadas desde {env_path}")
else:
    logger.warning(f"Archivo .env no encontrado en {env_path}")
    load_dotenv()  # Intentar cargar desde el directorio actual

# Configuración de APIs de IA
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")

# Configuración de directorios y formatos
DEFAULT_OUTPUT_DIR = os.getenv("DEFAULT_OUTPUT_DIR", "output")
DEFAULT_FORMATS = os.getenv("DEFAULT_FORMATS", "markdown,html").split(",")

# Parámetros de procesamiento
MAX_SEGMENT_LENGTH = int(os.getenv("MAX_SEGMENT_LENGTH", 1000))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 0.1))
TOP_N_SECTIONS = int(os.getenv("TOP_N_SECTIONS", 3))

# Configuración para deployment
PORT = int(os.getenv("PORT", 5000))
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()

# Establecer nivel de log según configuración
logging.getLogger().setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

def get_config_as_dict():
    """
    Devuelve la configuración como un diccionario para debugging.
    
    Returns:
        dict: Configuración actual (con claves de API enmascaradas)
    """
    config = {
        "OPENAI_API_KEY": mask_api_key(OPENAI_API_KEY),
        "ANTHROPIC_API_KEY": mask_api_key(ANTHROPIC_API_KEY),
        "OPENAI_MODEL": OPENAI_MODEL,
        "ANTHROPIC_MODEL": ANTHROPIC_MODEL,
        "DEFAULT_OUTPUT_DIR": DEFAULT_OUTPUT_DIR,
        "DEFAULT_FORMATS": DEFAULT_FORMATS,
        "MAX_SEGMENT_LENGTH": MAX_SEGMENT_LENGTH,
        "SIMILARITY_THRESHOLD": SIMILARITY_THRESHOLD,
        "TOP_N_SECTIONS": TOP_N_SECTIONS,
        "PORT": PORT,
        "DEBUG_MODE": DEBUG_MODE,
        "LOG_LEVEL": LOG_LEVEL
    }
    return config

def mask_api_key(key):
    """
    Enmascara una clave de API para mostrarla de forma segura.
    
    Args:
        key (str): Clave de API
        
    Returns:
        str: Clave enmascarada (muestra solo primeros/últimos 4 caracteres)
    """
    if not key:
        return "No configurada"
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"

def validate_config():
    """
    Valida que las configuraciones críticas estén presentes.
    
    Returns:
        bool: True si la configuración es válida, False en caso contrario
    """
    valid = True
    
    # Verificar claves de API
    if not OPENAI_API_KEY and not ANTHROPIC_API_KEY:
        logger.warning("No se ha configurado ninguna clave de API (OPENAI_API_KEY, ANTHROPIC_API_KEY)")
        valid = False
    
    # Verificar directorios
    if not os.path.exists(DEFAULT_OUTPUT_DIR):
        try:
            os.makedirs(DEFAULT_OUTPUT_DIR)
            logger.info(f"Directorio de salida creado: {DEFAULT_OUTPUT_DIR}")
        except Exception as e:
            logger.error(f"Error al crear directorio de salida: {e}")
            valid = False
    
    return valid

# Validar configuración al importar el módulo
if __name__ != "__main__":
    config_valid = validate_config()
    if config_valid:
        logger.info("Configuración validada correctamente")
    else:
        logger.warning("Hay problemas con la configuración actual")

if __name__ == "__main__":
    # Mostrar configuración actual (para debugging)
    import json
    print(json.dumps(get_config_as_dict(), indent=2))
    validate_config()