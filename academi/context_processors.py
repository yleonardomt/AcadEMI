from .models import Notification, Cart, Question
from django.conf import settings


def header_counters(request):
    """Contadores del navbar (notificaciones sin leer, items del carrito,
    preguntas sin responder) disponibles en cada página, no solo en el
    dashboard."""
    if not request.user.is_authenticated:
        return {'demo_mode': settings.DEMO_CHECKOUT,
                'google_login_available': bool(settings.GOOGLE_OAUTH_CLIENT_ID and settings.GOOGLE_OAUTH_CLIENT_SECRET)}

    context = {
        'demo_mode': settings.DEMO_CHECKOUT,
        'google_login_available': bool(settings.GOOGLE_OAUTH_CLIENT_ID and settings.GOOGLE_OAUTH_CLIENT_SECRET),
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }

    if request.user.role == 'student':
        cart = Cart.objects.filter(student=request.user).first()
        context['cart_items'] = cart.items.count() if cart else 0

    if request.user.role == 'teacher':
        context['pending_questions'] = Question.objects.filter(
            lesson__module__course__teacher=request.user, is_answered=False
        ).count()

    return context
