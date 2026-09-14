import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

GROQ_ENDPOINT = 'https://api.groq.com/openai/v1/chat/completions'
REQUEST_TIMEOUT = 8  # segundos


def is_ai_enabled():
    return bool(settings.GROQ_API_KEY)


def build_system_prompt(platform_context):
    """Arma el prompt de sistema con datos reales de la plataforma
    (RF-79, RF-80, RF-81) para que el asistente responda con contexto,
    similar a cómo Udemy conecta su asistente a su catálogo real."""
    lines = [
        "Eres el asistente virtual de AcadEMI, una plataforma educativa online de Bolivia.",
        "Responde en español, de forma breve, clara y amable (2-4 oraciones).",
        "Solo puedes ayudar con temas de AcadEMI: cursos, categorías, compras, "
        "progreso académico, certificados y uso general de la plataforma.",
        "Si no sabes algo con certeza, dilo y sugiere revisar la sección correspondiente "
        "del sitio en vez de inventar datos.",
        "",
        "Datos reales de la plataforma en este momento:",
        f"- Cursos publicados: {platform_context.get('total_courses', 0)}",
        f"- Categorías disponibles: {', '.join(platform_context.get('categories', [])) or 'sin datos'}",
    ]

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
    Genera una respuesta con IA (Groq, capa gratuita) usando datos reales
    de la plataforma como contexto. Devuelve None si la IA no está
    configurada o si falla la llamada, para que el llamador use el
    respaldo de palabras clave (ChatKnowledgeBase) sin interrumpir al
    usuario.
    """
    if not is_ai_enabled():
        return None

    messages = [{'role': 'system', 'content': build_system_prompt(platform_context)}]
    for turn in (history or [])[-6:]:
        messages.append(turn)
    messages.append({'role': 'user', 'content': user_message})

    try:
        response = requests.post(
            GROQ_ENDPOINT,
            headers={
                'Authorization': f'Bearer {settings.GROQ_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': settings.GROQ_MODEL,
                'messages': messages,
                'temperature': 0.4,
                'max_tokens': 300,
            },
            timeout=REQUEST_TIMEOUT,
        )
        if not response.ok:
            # El texto de la respuesta trae el motivo real (modelo inválido,
            # cuota agotada, IP bloqueada por Groq, etc.) — Response.raise_for_status()
            # por sí solo no lo deja en el traceback, así que se registra aparte
            # para poder diagnosticar sin tener que reproducir la llamada a mano.
            logger.error(
                'La IA del chatbot respondió %s: %s. Se usa el respaldo por palabras clave.',
                response.status_code, response.text[:500],
            )
            return None
        data = response.json()
        return data['choices'][0]['message']['content'].strip()
    except Exception:
        logger.exception('Fallo la llamada a la IA del chatbot; se usa el respaldo por palabras clave.')
        return None
