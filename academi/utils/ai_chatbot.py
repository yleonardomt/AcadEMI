import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


# Se usa la API de Gemini (Google AI Studio, capa gratuita) directo, en
# vez de vía OpenRouter: el pool gratuito de OpenRouter devolvía 404
# (modelo retirado), 429 (rate-limit compartido) o 502 (proveedor
# saturado) según el modelo probado. Con la key propia de Gemini se
# evita depender de ese pool compartido.
GEMINI_ENDPOINT = 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
REQUEST_TIMEOUT = 15  # segundos — la capa gratuita de Gemini a veces tarda 7-8s


def is_ai_enabled():
    return bool(settings.GEMINI_API_KEY)


def build_system_prompt(platform_context):
    """Arma el prompt de sistema con datos reales de la plataforma
    (RF-79, RF-80, RF-81) para que el asistente responda con contexto,
    similar a cómo Udemy conecta su asistente a su catálogo real."""
    lines = [
        "Eres el asistente virtual de AcadEMI, una plataforma educativa online de Bolivia.",
        "Responde en español, de forma breve, clara, amable y natural (2-4 oraciones), "
        "como una conversación real, no como un menú de opciones.",
        "Solo puedes ayudar con temas de AcadEMI: cursos, categorías, compras, "
        "progreso académico, certificados y uso general de la plataforma.",
        "Cuando el usuario cuente un gusto o interés (por ejemplo 'me gusta programar' "
        "o 'quiero aprender diseño'), interpreta a qué categoría del catálogo real de "
        "abajo corresponde y recomienda 1 a 3 cursos concretos de esa categoría por su "
        "nombre y precio exactos, en tono cercano (ej. 'te recomiendo estos cursos: ...'). "
        "Nunca inventes un curso, precio o categoría que no esté en el catálogo real.",
        "Si no sabes algo con certeza, dilo y sugiere revisar la sección correspondiente "
        "del sitio en vez de inventar datos.",
        "Nunca uses emojis: la interfaz de AcadEMI no los usa en ningún lado (usa iconos "
        "Font Awesome en su lugar), así que tu respuesta debe ser solo texto plano.",
        "",
        "Datos reales de la plataforma en este momento:",
        f"- Cursos publicados: {platform_context.get('total_courses', 0)}",
        f"- Categorías disponibles: {', '.join(platform_context.get('categories', [])) or 'sin datos'}",
    ]

    catalog = platform_context.get('catalog') or []
    if catalog:
        lines.append("- Catálogo real (categoría: cursos disponibles con precio):")
        for entry in catalog:
            lines.append(f"  · {entry['category']}: {', '.join(entry['courses'])}")

    if platform_context.get('is_authenticated'):
        lines.append(f"- El usuario que te escribe se llama: {platform_context.get('username', '')}")
        enrolled = platform_context.get('enrolled_courses', [])
        if enrolled:
            lines.append("- Cursos del usuario y su progreso:")
            for course in enrolled:
                lines.append(f"  · {course['title']}: {course['progress']}% completado")
        else:
            lines.append("- El usuario todavía no compró ningún curso.")

    return "\n".join(lines)


def get_ai_response(user_message, platform_context, history=None):
    """
    Genera una respuesta con IA (Gemini, capa gratuita) usando datos
    reales de la plataforma como contexto. Devuelve None si la IA no
    está configurada o si falla la llamada, para que el llamador use el
    respaldo de palabras clave (ChatKnowledgeBase) sin interrumpir al
    usuario.
    """
    if not is_ai_enabled():
        return None

    # La API de Gemini no tiene un rol "system": el prompt de sistema va
    # aparte en "systemInstruction", y el historial usa "model" en vez
    # de "assistant" para los turnos del bot.
    contents = []
    for turn in (history or [])[-6:]:
        role = 'model' if turn['role'] == 'assistant' else 'user'
        contents.append({'role': role, 'parts': [{'text': turn['content']}]})
    contents.append({'role': 'user', 'parts': [{'text': user_message}]})

    try:
        response = requests.post(
            GEMINI_ENDPOINT.format(model=settings.GEMINI_MODEL),
            params={'key': settings.GEMINI_API_KEY},
            headers={'Content-Type': 'application/json'},
            json={
                'systemInstruction': {'parts': [{'text': build_system_prompt(platform_context)}]},
                'contents': contents,
                'generationConfig': {'temperature': 0.4, 'maxOutputTokens': 300},
            },
            timeout=REQUEST_TIMEOUT,
        )
        if not response.ok:
            # El texto de la respuesta trae el motivo real (modelo inválido,
            # cuota agotada, etc.) — Response.raise_for_status() por sí solo
            # no lo deja en el traceback, así que se registra aparte para
            # poder diagnosticar sin tener que reproducir la llamada a mano.
            logger.error(
                'La IA del chatbot (Gemini) respondió %s: %s. Se usa el respaldo por palabras clave.',
                response.status_code, response.text[:500],
            )
            return None
        data = response.json()
        candidates = data.get('candidates') or []
        if not candidates:
            # Puede pasar por un bloqueo de seguridad (finishReason=SAFETY)
            # en vez de un error HTTP: sin candidatos no hay texto que usar.
            logger.error('La IA del chatbot (Gemini) no devolvió candidatos: %s', data)
            return None
        parts = candidates[0].get('content', {}).get('parts', [])
        text = ''.join(part.get('text', '') for part in parts).strip()
        return text or None
    except Exception:
        logger.exception('Fallo la llamada a la IA del chatbot; se usa el respaldo por palabras clave.')
        return None
