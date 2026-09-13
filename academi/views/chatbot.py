import time
import unicodedata

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ..models import (
    ChatSession, ChatMessage, ChatKnowledgeBase, ChatIntent, ChatAnalytics,
    Course, Category, Enrollment,
)
from ..utils.ai_chatbot import get_ai_response

STOPWORDS = {'y', 'e', 'de', 'del', 'la', 'el', 'los', 'las', 'en'}


def _normalize(text):
    """Minúsculas y sin tildes, para comparar sin importar acentos
    ("programación" vs. "programacion")."""
    stripped = ''.join(
        c for c in unicodedata.normalize('NFD', text.lower())
        if unicodedata.category(c) != 'Mn'
    )
    return stripped


# ============================================
# MÓDULO 10: ASISTENTE VIRTUAL (RF-77 al RF-82)
# ============================================
def chatbot_view(request):
    return render(request, 'academi/chatbot/chatbot.html')


def recommend_courses_by_category(user_message):
    """RF-79: si el mensaje menciona una categoría real (o una palabra
    significativa de su nombre), responde con cursos publicados reales
    de esa categoría (título y precio) en vez de un texto genérico
    desconectado del catálogo real."""
    text = _normalize(user_message)

    for category in Category.objects.all():
        words = [
            _normalize(w) for w in category.name.split()
            if len(w) > 3 and w.lower() not in STOPWORDS
        ]
        if not any(word in text for word in words):
            continue

        courses = Course.objects.filter(status='published', category=category)[:3]
        if not courses:
            continue

        lines = [f'{c.title} ({c.get_price_display()})' for c in courses]
        return (
            f'En la categoría "{category.name}" tenemos, entre otros: '
            + '; '.join(lines) + '. Puedes verlos todos en el catálogo filtrando por esa categoría.'
        )

    return None


def _keyword_score(keywords_field, text_words):
    """Cuenta cuántas de las frases clave "encajan" en el mensaje: una
    frase encaja si la mayoría de sus palabras (no solo una coincidencia
    literal de la frase completa) aparecen en el mensaje. Esto tolera
    variaciones normales del lenguaje ("hablar con UN docente" vs.
    "hablar con EL docente", "me inscribo" vs. "inscribirme") que una
    comparación de substring exacta no detecta."""
    score = 0
    for phrase in keywords_field.split(','):
        phrase_words = [w for w in _normalize(phrase).split() if w]
        if not phrase_words:
            continue
        matched = sum(1 for w in phrase_words if w in text_words)
        if matched / len(phrase_words) >= 0.6:
            score += 1
    return score


def match_knowledge_base(user_message):
    """RF-78 al RF-82: hace coincidir el mensaje del usuario contra la base
    de conocimiento (o, en su defecto, las intenciones) por palabras clave."""
    recommendation = recommend_courses_by_category(user_message)
    if recommendation:
        return recommendation

    text_words = set(_normalize(user_message).split())

    best_answer = None
    best_score = 0

    for entry in ChatKnowledgeBase.objects.filter(is_active=True):
        score = _keyword_score(entry.keywords, text_words)
        if score > best_score:
            best_score = score
            best_answer = entry.answer

    if best_answer:
        return best_answer

    for intent in ChatIntent.objects.filter(is_active=True):
        score = _keyword_score(intent.keywords, text_words)
        if score > best_score:
            best_score = score
            best_answer = intent.response_template

    if best_answer:
        return best_answer

    return (
        'Gracias por tu mensaje. Puedo ayudarte con información sobre cursos, '
        'el proceso de compra, tu progreso académico o el uso general de la plataforma. '
        '¿Sobre cuál te gustaría saber más?'
    )


def build_platform_context(user):
    """RF-79, RF-80, RF-81: datos reales de la plataforma para que el
    asistente (con o sin IA) responda con información actual, en vez de
    respuestas genéricas desconectadas del sitio real."""
    context = {
        'total_courses': Course.objects.filter(status='published').count(),
        'categories': list(Category.objects.values_list('name', flat=True)[:12]),
        'is_authenticated': user.is_authenticated,
    }
    if user.is_authenticated:
        context['username'] = user.get_full_name() or user.username
        context['enrolled_courses'] = [
            {'title': e.course.title, 'progress': e.progress_percentage}
            for e in Enrollment.objects.filter(student=user).select_related('course')[:8]
        ]
    return context


def get_chat_history(session):
    """Últimos turnos de la conversación, en el formato que espera la IA."""
    history = []
    for msg in session.messages.order_by('-created_at')[:6][::-1]:
        history.append({
            'role': 'assistant' if msg.sender == 'bot' else 'user',
            'content': msg.message,
        })
    return history


@require_POST
def chatbot_send_message(request):
    """RF-78: recibir preguntas y responder; persiste la conversación
    cuando el usuario tiene sesión iniciada (RF-77). Intenta responder
    con IA (si está configurada, ver academi/utils/ai_chatbot.py) usando
    datos reales de la plataforma como contexto; si la IA no está
    disponible o falla, usa la base de conocimiento por palabras clave
    sin que el usuario note la diferencia."""
    user_message = request.POST.get('message', '').strip()
    if not user_message:
        return JsonResponse({'success': False, 'message': 'Escribe un mensaje.'})

    session = None
    history = None
    if request.user.is_authenticated:
        session, _ = ChatSession.objects.get_or_create(
            user=request.user, is_active=True,
            defaults={},
        )
        history = get_chat_history(session)

    start = time.time()
    platform_context = build_platform_context(request.user)
    bot_response = get_ai_response(user_message, platform_context, history)
    used_ai = bot_response is not None
    if not bot_response:
        bot_response = match_knowledge_base(user_message)
    response_time = round(time.time() - start, 3)

    if session:
        ChatMessage.objects.create(session=session, sender='user', message=user_message)
        bot_msg = ChatMessage.objects.create(
            session=session, sender='bot', message=bot_response, response_time=response_time
        )

        analytics, _ = ChatAnalytics.objects.get_or_create(session=session)
        analytics.total_messages = session.messages.count()
        analytics.user_messages = session.messages.filter(sender='user').count()
        analytics.bot_messages = session.messages.filter(sender='bot').count()
        analytics.save()

        return JsonResponse({
            'success': True, 'response': bot_response, 'message_id': bot_msg.id, 'ai': used_ai,
        })

    return JsonResponse({'success': True, 'response': bot_response, 'message_id': None, 'ai': used_ai})
