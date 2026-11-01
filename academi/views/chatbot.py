import re
import time
import unicodedata

from django.core.cache import cache
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.conf import settings

from ..models import (
    ChatSession, ChatMessage, ChatKnowledgeBase, ChatIntent, ChatAnalytics, ChatFeedback,
    Course, Category, Enrollment,
)
from ..utils.ai_chatbot import get_ai_response

STOPWORDS = {'y', 'e', 'de', 'del', 'la', 'el', 'los', 'las', 'en'}
MAX_MESSAGE_LENGTH = 1000

_PUNCTUATION_RE = re.compile(r'[^\w\s]', re.UNICODE)


def _normalize(text):
    """Minúsculas, sin tildes y sin puntuación, para comparar sin
    importar acentos ("programación" vs. "programacion") ni signos
    ("¿cuánto cuesta?" vs. "cuanto cuesta") — sin esto, "emi?" o
    "¿tengo" nunca calzaban con las palabras clave "emi"/"tengo"
    porque el signo quedaba pegado a la palabra."""
    stripped = ''.join(
        c for c in unicodedata.normalize('NFD', text.lower())
        if unicodedata.category(c) != 'Mn'
    )
    return _PUNCTUATION_RE.sub(' ', stripped)


# ============================================
# MÓDULO 10: ASISTENTE VIRTUAL (RF-77 al RF-82)
# ============================================
def chatbot_view(request):
    messages = []
    if request.user.is_authenticated:
        session = ChatSession.objects.filter(user=request.user, is_active=True).order_by('-id').first()
        if session:
            messages = list(session.messages.order_by('-id')[:40][::-1])
    return render(request, 'academi/chatbot/chatbot.html', {'chat_messages': messages})


def _stem_match(category_word, text_word, stem_len=6):
    """Compara dos palabras por su raíz en vez de exigir que sean
    idénticas: sin esto, "programar" nunca calzaba con la categoría
    "Programación" (son formas distintas de la misma palabra, y una
    no es substring literal de la otra), así que un mensaje tan básico
    como "me gusta programar" no recibía ninguna recomendación."""
    if len(category_word) < 4 or len(text_word) < 4:
        return category_word == text_word
    n = min(len(category_word), len(text_word), stem_len)
    return category_word[:n] == text_word[:n]


def recommend_courses_by_category(user_message):
    """RF-79: si el mensaje menciona una categoría real (o una palabra
    significativa de su nombre, incluso en otra forma gramatical:
    "programar" también debe calzar con la categoría "Programación"),
    responde con cursos publicados reales de esa categoría (título y
    precio) en vez de un texto genérico desconectado del catálogo real."""
    text_words = _normalize(user_message).split()
    # Una pregunta de compra o soporte que mencione una materia no es
    # necesariamente una petición de recomendaciones.
    if len(text_words) > 3 and not set(text_words) & {
        'recomienda', 'recomiendas', 'recomendacion', 'aprender', 'estudiar',
        'interesa', 'gusta', 'busco', 'quiero', 'cursos', 'curso',
    }:
        return None

    for category in Category.objects.all():
        words = [
            _normalize(w) for w in category.name.split()
            if len(w) > 3 and w.lower() not in STOPWORDS
        ]
        if not any(_stem_match(word, tw) for word in words for tw in text_words):
            continue

        courses = Course.objects.filter(status='published', category=category).order_by('title')[:3]
        if not courses:
            continue

        lines = [f'{c.title} ({c.get_price_display()})' for c in courses]
        return (
            f'En la categoría "{category.name}" tenemos, entre otros: '
            + '; '.join(lines) + '. Puedes verlos todos en el catálogo filtrando por esa categoría.'
        )

    # Si ninguna categoría calzó (p.ej. "inglés" no aparece en el nombre
    # de la categoría "Idiomas y Comunicación"), se busca también por
    # palabras del título de un curso real, para no depender solo del
    # nombre de la categoría.
    for course in Course.objects.filter(status='published').select_related('category'):
        words = [
            _normalize(w) for w in course.title.split()
            if len(w) > 3 and w.lower() not in STOPWORDS
        ]
        if not any(_stem_match(word, tw) for word in words for tw in text_words):
            continue

        courses = Course.objects.filter(status='published', category=course.category).order_by('title')[:3]
        lines = [f'{c.title} ({c.get_price_display()})' for c in courses]
        return (
            f'En la categoría "{course.category.name}" tenemos, entre otros: '
            + '; '.join(lines) + '. Puedes verlos todos en el catálogo filtrando por esa categoría.'
        )

    return None


def _keyword_score(keywords_field, text_words):
    """Cuenta cuántas de las frases clave "encajan" en el mensaje: una
    frase encaja si la mayoría de sus palabras (no solo una coincidencia
    literal de la frase completa) aparecen en el mensaje. Esto tolera
    variaciones normales del lenguaje ("hablar con UN docente" vs.
    "hablar con EL docente", "me inscribo" vs. "inscribirme") que una
    comparación de substring exacta no detecta.

    El puntaje suma la cantidad de palabras coincidentes de cada frase
    que encaja (no solo +1 por frase): así una frase específica de 2-3
    palabras ("descuento emi") pesa más que una genérica de 1 sola
    palabra ("descuento"), y una entrada más específica gana el
    desempate frente a una genérica cuando ambas encajan."""
    score = 0
    for phrase in keywords_field.split(','):
        phrase_words = [w for w in _normalize(phrase).split() if w]
        if not phrase_words:
            continue
        matched = sum(1 for w in phrase_words if w in text_words)
        if matched / len(phrase_words) >= 0.6:
            score += matched
    return score


def match_knowledge_base(user_message):
    """RF-78 al RF-82: hace coincidir el mensaje del usuario contra la base
    de conocimiento (o, en su defecto, las intenciones) por palabras clave."""
    text_words = set(_normalize(user_message).split())
    if text_words & {'comprar', 'compra', 'pagar', 'pago', 'tarjeta', 'qr', 'metodos', 'carrito', 'cupon', 'descuento', 'promocion', 'oferta'} and not text_words & {'historial', 'comprobante', 'factura'}:
        if settings.DEMO_CHECKOUT:
            if 'emi' in text_words and text_words & {'descuento', 'cupon'}:
                return ('Con un correo @est.emi.edu.bo se aplica un 15% de descuento en la primera compra paga. '
                        'También puedes usar un cupón vigente; se aplica el descuento mayor. Revisa el total en el carrito.')
            return ('Agrega los cursos al carrito, aplica un cupón si tienes uno y completa la compra desde allí. '
                    'El total se calcula con los precios y descuentos vigentes.')
        if 'emi' in text_words and text_words & {'descuento', 'cupon'}:
            return ('El descuento EMI previsto es del 15% para la primera compra con correo @est.emi.edu.bo. '
                    'Las compras de cursos pagos aún no están habilitadas; puedes inscribirte en cursos gratuitos.')
        return ('Las compras de cursos pagos aún no están habilitadas. '
                'Puedes inscribirte en cursos gratuitos y consultar el catálogo mientras se integra un cobro verificable.')
    if text_words & {'cursos', 'catalogo', 'disponibles'} and not text_words & {'comprar', 'pagar', 'precio', 'descuento'}:
        published = Course.objects.filter(status='published').order_by('title')
        count = published.count()
        if not count:
            return 'Todavía no hay cursos publicados. Puedes volver a consultar el catálogo más adelante.'
        names = '; '.join(f'{c.title} ({c.get_price_display()})' for c in published[:5])
        return f'Hay {count} cursos publicados. Algunos son: {names}. Consulta el catálogo para ver todos los cursos y precios actuales.'

    recommendation = recommend_courses_by_category(user_message)
    if recommendation:
        return recommendation

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


def build_platform_context():
    """Muestra pública del catálogo actual para preguntas abiertas a la IA."""
    catalog = []
    for category in Category.objects.all():
        courses = Course.objects.filter(status='published', category=category).order_by('title')[:4]
        if courses:
            catalog.append({
                'category': category.name,
                'courses': [f'{c.title} ({c.get_price_display()})' for c in courses],
            })

    context = {
        'total_courses': Course.objects.filter(status='published').count(),
        'categories': list(Category.objects.values_list('name', flat=True)[:12]),
        'catalog': catalog,
    }
    return context


def personal_answer(user, user_message):
    """Consulta datos de la cuenta sin enviarlos a un proveedor externo."""
    words = set(_normalize(user_message).split())
    if not words & {'mis', 'mi'} or not words & {'cursos', 'curso', 'progreso', 'avance'}:
        return None
    if not user.is_authenticated:
        return 'Inicia sesión para consultar tus cursos y tu progreso.'
    enrollments = Enrollment.objects.filter(
        student=user, status__in=('enrolled', 'in_progress', 'completed')
    ).select_related('course').order_by('-id')[:8]
    if not enrollments:
        return 'Todavía no tienes cursos inscritos. Puedes explorar el catálogo para encontrar uno.'
    rows = '; '.join(f'{e.course.title}: {e.progress_percentage}% completado' for e in enrollments)
    return f'Tus cursos recientes y su progreso: {rows}. En Mi progreso puedes ver el detalle.'


def _rate_limited(request):
    identity = f'user:{request.user.pk}' if request.user.is_authenticated else f'ip:{request.META.get("REMOTE_ADDR", "unknown")}'
    key = f'chat-rate:{identity}'
    if cache.add(key, 1, 60):
        return False
    try:
        return cache.incr(key) > 20
    except ValueError:
        cache.set(key, 1, 60)
        return False


def answer_chat(request, user_message):
    """Una sola ruta de respuesta para web y API móvil."""
    if not isinstance(user_message, str):
        return None, 'El mensaje debe ser texto.', 400
    user_message = user_message.strip()
    if not user_message:
        return None, 'Escribe un mensaje.', 400
    if len(user_message) > MAX_MESSAGE_LENGTH:
        return None, f'El mensaje debe tener como máximo {MAX_MESSAGE_LENGTH} caracteres.', 400
    if _rate_limited(request):
        return None, 'Has enviado muchos mensajes. Espera un minuto e inténtalo de nuevo.', 429

    session = None
    history = None
    if request.user.is_authenticated:
        session = ChatSession.objects.filter(user=request.user, is_active=True).order_by('-id').first()
        if session is None:
            session = ChatSession.objects.create(user=request.user)
        history = get_chat_history(session)

    start = time.monotonic()
    # Las respuestas conocidas salen de datos locales verificables. La IA
    # atiende preguntas abiertas y recibe los datos actuales del catálogo.
    known_answer = personal_answer(request.user, user_message) or match_knowledge_base(user_message)
    fallback = known_answer.startswith('Gracias por tu mensaje.')
    bot_response = None if fallback else known_answer
    used_ai = False
    if bot_response is None:
        bot_response = get_ai_response(user_message, build_platform_context(), history)
        used_ai = bool(bot_response)
    if not bot_response:
        bot_response = known_answer
    response_time = round(time.monotonic() - start, 3)

    bot_msg = None
    if session:
        ChatMessage.objects.create(session=session, sender='user', message=user_message)
        bot_msg = ChatMessage.objects.create(session=session, sender='bot', message=bot_response, response_time=response_time)
        analytics, _ = ChatAnalytics.objects.get_or_create(session=session)
        analytics.total_messages += 2
        analytics.user_messages += 1
        analytics.bot_messages += 1
        analytics.avg_response_time = round(
            ((analytics.avg_response_time * (analytics.bot_messages - 1)) + response_time) / analytics.bot_messages, 3
        )
        analytics.save()
    return {'response': bot_response, 'message_id': bot_msg.id if bot_msg else None, 'ai': used_ai}, None, 200


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
    """Responde con datos locales y usa IA para preguntas abiertas."""
    data, error, status = answer_chat(request, request.POST.get('message', ''))
    return JsonResponse({'success': not error, **(data or {'message': error})}, status=status)


@login_required
@require_POST
def chatbot_feedback(request):
    try:
        rating = int(request.POST.get('rating', ''))
        message_id = int(request.POST.get('message_id', ''))
    except (TypeError, ValueError):
        return JsonResponse({'success': False, 'message': 'Valoración inválida.'}, status=400)
    if rating not in (1, 2, 3, 4, 5):
        return JsonResponse({'success': False, 'message': 'Valoración inválida.'}, status=400)
    message = ChatMessage.objects.filter(pk=message_id, sender='bot', session__user=request.user).first()
    if not message:
        return JsonResponse({'success': False, 'message': 'Mensaje no encontrado.'}, status=404)
    ChatFeedback.objects.update_or_create(message=message, user=request.user, defaults={'rating': rating})
    return JsonResponse({'success': True})
