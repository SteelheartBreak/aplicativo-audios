import os
import speech_recognition as sr
from pydub import AudioSegment
import math
import time

def convertir_m4a_a_wav(ruta_m4a, ruta_wav="audio_convertido.wav"):
    """
    Convierte un archivo M4A a formato WAV para poder procesarlo con SpeechRecognition
    """
    try:
        print(f"Intentando convertir {ruta_m4a} a WAV...")
        audio = AudioSegment.from_file(ruta_m4a, format="m4a")
        audio.export(ruta_wav, format="wav")
        print(f"Conversión exitosa. Archivo WAV guardado en: {ruta_wav}")
        return ruta_wav
    except Exception as e:
        print(f"Error al convertir M4A a WAV: {e}")
        return None

def transcribir_audio_por_segmentos(ruta_audio, ruta_salida="transcripcion.txt", idioma="es-ES", duracion_segmento=30):
    """
    Transcribe un archivo de audio a texto dividiéndolo en segmentos
    y guarda cada segmento transcrito en el archivo de salida
    """
    recognizer = sr.Recognizer()
    
    try:
        # Abrir el archivo de texto en modo de escritura
        with open(ruta_salida, "w", encoding="utf-8") as archivo_salida:
            archivo_salida.write("TRANSCRIPCIÓN EN PROGRESO...\n\n")
        
        # Cargar el audio completo
        audio_completo = AudioSegment.from_wav(ruta_audio)
        duracion_total = len(audio_completo) / 1000  # Duración en segundos
        
        # Calcular número de segmentos
        num_segmentos = math.ceil(duracion_total / duracion_segmento)
        
        print(f"El audio tiene una duración de {duracion_total:.2f} segundos")
        print(f"Dividiendo en {num_segmentos} segmentos de {duracion_segmento} segundos")
        
        # Inicializar contador de tiempo
        tiempo_inicio_total = time.time()
        
        for i in range(num_segmentos):
            # Marcar tiempo de inicio para este segmento
            tiempo_inicio_segmento = time.time()
            
            # Extraer segmento
            inicio_ms = i * duracion_segmento * 1000
            fin_ms = min((i + 1) * duracion_segmento * 1000, len(audio_completo))
            segmento = audio_completo[inicio_ms:fin_ms]
            
            # Convertir milisegundos a formato de tiempo legible
            inicio_tiempo = time.strftime('%H:%M:%S', time.gmtime(inicio_ms/1000))
            fin_tiempo = time.strftime('%H:%M:%S', time.gmtime(fin_ms/1000))
            
            # Guardar segmento temporalmente
            archivo_segmento = f"segmento_temp_{i}.wav"
            segmento.export(archivo_segmento, format="wav")
            
            print(f"Procesando segmento {i+1}/{num_segmentos} [{inicio_tiempo} - {fin_tiempo}]...")
            
            # Transcribir segmento
            texto_segmento = ""
            with sr.AudioFile(archivo_segmento) as source:
                audio_data = recognizer.record(source)
                try:
                    texto_segmento = recognizer.recognize_google(audio_data, language=idioma)
                    print(f"Segmento {i+1} transcrito exitosamente")
                except sr.UnknownValueError:
                    texto_segmento = "[inaudible]"
                    print(f"No se pudo entender el audio en el segmento {i+1}")
                except sr.RequestError as e:
                    texto_segmento = "[error de servicio]"
                    print(f"Error en la solicitud para el segmento {i+1}: {e}")
            
            # Eliminar archivo temporal del segmento
            try:
                os.remove(archivo_segmento)
            except:
                pass
            
            # Añadir el texto transcrito al archivo de salida
            with open(ruta_salida, "a", encoding="utf-8") as archivo_salida:
                archivo_salida.write(f"[{inicio_tiempo} - {fin_tiempo}]: {texto_segmento}\n\n")
            
            # Calcular tiempo transcurrido para este segmento
            tiempo_segmento = time.time() - tiempo_inicio_segmento
            print(f"Tiempo para segmento {i+1}: {tiempo_segmento:.2f} segundos")
            print(f"Texto añadido al archivo: {ruta_salida}")
            print("-" * 50)
                
    except Exception as e:
        print(f"Error durante la transcripción por segmentos: {e}")
        with open(ruta_salida, "a", encoding="utf-8") as archivo_salida:
            archivo_salida.write(f"\n[ERROR] Transcripción interrumpida: {e}\n")
    
    # Calcular tiempo total
    tiempo_total = time.time() - tiempo_inicio_total
    print(f"\nTranscripción completada en {tiempo_total:.2f} segundos")
    
    # Marcar como completado en el archivo
    with open(ruta_salida, "a", encoding="utf-8") as archivo_salida:
        archivo_salida.write("\n\nTRANSCRIPCIÓN COMPLETADA\n")
        archivo_salida.write(f"Tiempo total: {tiempo_total:.2f} segundos\n")
    
    return True

def m4a_a_texto(ruta_m4a, ruta_salida="transcripcion.txt", idioma="es-ES"):
    """
    Función principal para convertir un archivo M4A a texto
    """
    print(f"Procesando el archivo de audio: {ruta_m4a}")
    
    # Comprobar que el archivo existe
    if not os.path.isfile(ruta_m4a):
        print(f"¡ERROR! El archivo {ruta_m4a} no existe o no es accesible.")
        with open(ruta_salida, "w", encoding="utf-8") as archivo:
            archivo.write(f"Error: No se encontró el archivo {ruta_m4a}. Verifica la ruta y el nombre del archivo.")
        return False
    
    # Convertir M4A a WAV
    ruta_wav = convertir_m4a_a_wav(ruta_m4a)
    if not ruta_wav:
        with open(ruta_salida, "w", encoding="utf-8") as archivo:
            archivo.write("Error al convertir el archivo M4A a WAV.")
        return False
    
    # Transcribir el audio a texto
    resultado = transcribir_audio_por_segmentos(ruta_wav, ruta_salida, idioma)
    
    # Limpiar archivos temporales
    try:
        os.remove(ruta_wav)
        print(f"Archivo temporal {ruta_wav} eliminado.")
    except Exception as e:
        print(f"No se pudo eliminar el archivo temporal: {e}")
    
    return resultado

# Ejemplo de uso con tu archivo específico
if __name__ == "__main__":
    # Nombre del archivo de audio
    ruta_del_audio = "audio.m4a"
    
    # Nombre del archivo de salida
    archivo_salida = "transcripcion.txt"
    
    # Idioma del audio (es-ES para español, en-US para inglés, etc.)
    idioma = "es-ES"
    
    print("Iniciando proceso de transcripción progresiva...")
    resultado = m4a_a_texto(ruta_del_audio, archivo_salida, idioma)
    
    if resultado:
        print(f"\nLa transcripción se ha guardado en '{archivo_salida}'")
        print("La transcripción se ha ido guardando segmento por segmento.")
    else:
        print("No se pudo realizar la transcripción correctamente.")