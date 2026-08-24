"""
ai_coach.py
Módulo de integración con la API de Google Gemini para APP GYM.

Requiere: pip install -U google-genai
Variable de entorno: GEMINI_API_KEY
"""

import os
import json
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai import errors as genai_errors

# Carga las variables definidas en el archivo .env (si existe) al entorno
# del proceso. En producción/despliegue, las variables de entorno pueden
# venir ya configuradas por la plataforma y esta llamada simplemente no
# encuentra archivo .env y no hace nada.
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_coach")

# --------------------------------------------------------------------------
# Configuración
# --------------------------------------------------------------------------

# La API key SIEMPRE se lee de la variable de entorno GEMINI_API_KEY,
# nunca escrita a mano aquí (este archivo se sube a GitHub).
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "TU_API_KEY_AQUI")

# Modelo estable vigente (agosto 2026). No usar gemini-2.5-*, 2.0-*, 1.5-*
# (retirados). Si necesitas más capacidad de razonamiento a costa de
# velocidad, la alternativa es "gemini-3.1-pro-preview".
MODEL_ID = "gemini-3.6-flash"


class AICoachError(Exception):
    """Excepción de dominio para fallos de la capa IA, pensada para ser
    capturada limpiamente en app.py sin tumbar la sesión de Streamlit."""
    pass


def _validar_api_key():
    if not GEMINI_API_KEY or GEMINI_API_KEY == "TU_API_KEY_AQUI":
        raise AICoachError(
            "No se ha configurado GEMINI_API_KEY. Define la variable de "
            "entorno antes de lanzar la app (ej. en un archivo .env o "
            "export GEMINI_API_KEY=...)."
        )


def _crear_cliente() -> genai.Client:
    """Crea el cliente de Gemini usando la versión estable de la API
    (v1beta, por defecto del SDK). NO forzar v1alpha aquí: esa superficie
    corresponde a la Interactions API (agentes), no a generate_content,
    y provoca 404 con los modelos estándar."""
    _validar_api_key()
    return genai.Client(api_key=GEMINI_API_KEY)


def _generar(prompt: str, json_mode: bool = False) -> str:
    """Punto único de llamada al modelo, con manejo defensivo de errores
    de red / API. Lanza AICoachError con un mensaje legible para mostrar
    en la UI de Streamlit (st.error), en vez de propagar la excepción
    cruda del SDK."""
    try:
        client = _crear_cliente()
        config = None
        if json_mode:
            config = types.GenerateContentConfig(response_mime_type="application/json")

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=config,
        )
        if not response or not response.text:
            raise AICoachError(
                "El modelo respondió vacío. Puede ser un bloqueo de "
                "seguridad del contenido o un fallo temporal del servicio."
            )
        return response.text

    except genai_errors.ClientError as e:
        logger.error("Error de cliente Gemini: %s", e)
        raise AICoachError(
            f"La API de Gemini rechazó la solicitud (posible modelo "
            f"incorrecto, API key inválida o cuota agotada). Detalle: {e}"
        ) from e

    except genai_errors.ServerError as e:
        logger.error("Error de servidor Gemini: %s", e)
        raise AICoachError(
            "El servicio de Gemini no está disponible en este momento. "
            "Inténtalo de nuevo en unos segundos."
        ) from e

    except genai_errors.APIError as e:
        logger.error("Error de API Gemini: %s", e)
        raise AICoachError(f"Error de la API de Gemini: {e}") from e

    except AICoachError:
        raise

    except Exception as e:
        logger.exception("Error inesperado llamando a Gemini")
        raise AICoachError(
            f"Fallo de conexión o error inesperado al contactar con la "
            f"IA: {e}"
        ) from e


# --------------------------------------------------------------------------
# Agentes de dominio
# --------------------------------------------------------------------------

def analizar_entrenamiento(perfil, day_one, modificaciones, bloque_nombre,
                            ejercicios_desglose, sensaciones) -> str:
    """Agente Biomecánico: Audita la rutina por bloques, selección de
    ejercicios y progresión."""

    prompt = f"""
    Eres un entrenador personal de élite experto en Biomecánica, Hipertrofia y Fisiología del Ejercicio.

    **CONTEXTO DEL ATLETA:**
    - Perfil: {perfil[0]} | Edad: {perfil[1]} | Peso: {perfil[2]}kg | Objetivo: {perfil[3]} | Nivel: {perfil[4]}
    - Contexto Day One: Rutina habitual ({day_one[0] if day_one else 'N/A'})
    - Eventos/Lesiones recientes: {modificaciones}

    **SESIÓN DE HOY A EVALUAR (los ejercicios están listados en el ORDEN REAL en que se ejecutaron, de primero a último):**
    - Bloque de Entrenamiento: {bloque_nombre}
    - Desglose de Ejercicios y Series Realizadas (orden cronológico):
    {ejercicios_desglose}
    - Sensaciones / Molestias informadas: {sensaciones}

    **INSTRUCCIONES DE AUDITORÍA:**
    1. **Análisis Biomecánico:** Evalúa la selección de ejercicios dentro del bloque, respetando el orden real en que se realizaron. ¿Falta o sobra estímulo en algún vector de fuerza o perfil de resistencia?
    2. **Gestión del Esfuerzo (RIR/Fallo):** Revisa si la intensidad (RIR y series al fallo) fue adecuada para el objetivo.
    3. **Ajustes y Recomendaciones:** Da 2-3 consejos concisos para la próxima vez que le toque este mismo bloque.

    Responde en formato Markdown limpio, directo al grano y con tono profesional pero accesible.
    """
    return _generar(prompt)


def responder_flexibilidad_nutricional(tipo_consulta, macros_restantes,
                                        contexto_user) -> str:
    """Coach Nutricional: Ajustes flexibles de macros y alimentos
    disponibles (IIFYM)."""

    rem_k, rem_p, rem_c, rem_g = macros_restantes

    prompt = f"""
    Eres un Nutricionista Deportivo enfocado en Nutrición Flexible (IIFYM).

    **MACROS RESTANTES PARA EL DÍA:**
    - Calorías: {rem_k:.0f} kcal
    - Proteínas: {rem_p:.1f} g
    - Carbohidratos: {rem_c:.1f} g
    - Grasas: {rem_g:.1f} g

    **CONSULTA DEL ATLETA:**
    - Tipo: {tipo_consulta}
    - Detalle/Ingredientes disponibles: {contexto_user}

    Proporciona combinaciones exactas o sugerencias prácticas que le permitan cuadrar estos macros restantes sin estrés.
    """
    return _generar(prompt)


def auditar_progreso_longitudinal(perfil, tendencia_peso, resumen_entreno,
                                   recuperacion, objetivos_act) -> str:
    """Auditoría de 14 días: evalúa la tendencia biométrica y sugiere
    reajustes de macros."""

    prompt = f"""
    Eres un Director de Rendimiento Deportivo realizando la auditoría quincenal.

    **DATOS DE LOS ÚLTIMOS 14 DÍAS:**
    - Perfil: {perfil}
    - Histórico de Peso y Cintura: {tendencia_peso}
    - Resumen de Volumen de Entreno: {resumen_entreno}
    - Medias de Sueño/NEAT/Fatiga: {recuperacion}
    - Objetivos de Macros Actuales: {objetivos_act[0]} kcal | P: {objetivos_act[1]}g | C: {objetivos_act[2]}g | G: {objetivos_act[3]}g

    Haz una evaluación general del progreso y determina si se deben mantener o ajustar los macros actuales.
    """
    return _generar(prompt)


def estimar_macros_de_comida(descripcion: str) -> list:
    """Agente Nutricional Estimador: convierte una descripción de comida en
    lenguaje natural (ej. 'arroz con pollo, salsa de tomate y judías verdes')
    en una lista de alimentos desglosados con sus macros estimados.

    Devuelve una lista de dicts:
    [{"alimento": str, "cantidad_estimada": str, "kcal": float,
      "protein": float, "carbs": float, "fats": float}, ...]
    """
    if not descripcion or not descripcion.strip():
        raise AICoachError("Describe la comida antes de calcular los macros.")

    prompt = f"""
    Eres un nutricionista experto en estimar el contenido nutricional de comidas
    caseras a partir de una descripción en lenguaje natural, usando tablas
    nutricionales estándar y raciones habituales de una persona adulta.

    DESCRIPCIÓN DE LA COMIDA:
    "{descripcion.strip()}"

    Descompón la comida en los alimentos/ingredientes principales que la
    componen. Si el usuario no dio una cantidad exacta para alguno, asume una
    ración individual realista y normal (ni extra pequeña ni extra grande).
    Calcula los macros aproximados de cada componente.

    Responde ÚNICAMENTE con un JSON válido, sin texto adicional, sin backticks
    ni bloques de código, con esta estructura EXACTA:
    {{
      "items": [
        {{
          "alimento": "nombre del alimento o componente",
          "cantidad_estimada": "descripción breve de la ración, ej. '150g' o '1 filete mediano'",
          "kcal": 0,
          "protein": 0,
          "carbs": 0,
          "fats": 0
        }}
      ]
    }}
    Usa números (no strings, no unidades) para kcal, protein, carbs y fats.
    """

    texto = _generar(prompt, json_mode=True)

    # Limpieza defensiva por si el modelo añade backticks pese a la instrucción
    texto_limpio = texto.strip()
    if texto_limpio.startswith("```"):
        texto_limpio = texto_limpio.strip("`")
        if texto_limpio.lower().startswith("json"):
            texto_limpio = texto_limpio[4:]
        texto_limpio = texto_limpio.strip()

    try:
        data = json.loads(texto_limpio)
        items = data.get("items", [])
        if not items:
            raise ValueError("La IA no devolvió ningún alimento reconocible.")

        resultado = []
        for it in items:
            resultado.append({
                "alimento": str(it.get("alimento", "Alimento sin nombre")),
                "cantidad_estimada": str(it.get("cantidad_estimada", "ración estimada")),
                "kcal": float(it.get("kcal", 0) or 0),
                "protein": float(it.get("protein", 0) or 0),
                "carbs": float(it.get("carbs", 0) or 0),
                "fats": float(it.get("fats", 0) or 0),
            })
        return resultado

    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.error("Error parseando JSON de macros: %s | Texto: %s", e, texto)
        raise AICoachError(
            "No se pudo interpretar la respuesta de la IA como una lista de "
            "alimentos. Intenta describir la comida de forma un poco más "
            "clara (ej. separando los ingredientes por comas)."
        ) from e