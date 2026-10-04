"""RNF-17: registro de eventos de seguridad y autenticación del sitio web
(inicios y cierres de sesión, intentos fallidos). Los pagos y las acciones
administrativas se registran en las vistas / AdminAuditMiddleware."""
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from .models import ActivityLog
from .utils import get_client_ip


def _log(request, user, action, description):
    if user is None or not getattr(user, 'pk', None):
        return
    try:
        ActivityLog.objects.create(
            user=user, action_type=action, description=description,
            ip_address=get_client_ip(request) if request else None,
            user_agent=(request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''),
        )
    except Exception:
        pass  # el registro nunca debe romper el inicio de sesión


@receiver(user_logged_in)
def on_login(sender, request, user, **kwargs):
    _log(request, user, 'login', f'Inicio de sesión de {user.username}')


@receiver(user_logged_out)
def on_logout(sender, request, user, **kwargs):
    _log(request, user, 'logout', f'Cierre de sesión de {getattr(user, "username", "")}')


@receiver(user_login_failed)
def on_login_failed(sender, credentials, request=None, **kwargs):
    User = get_user_model()
    ident = credentials.get('username') or ''
    user = User.objects.filter(username=ident).first() or User.objects.filter(email__iexact=ident).first()
    _log(request, user, 'other', f'Intento de inicio de sesión fallido para "{ident}"')
