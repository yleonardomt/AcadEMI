"""Utilidades comunes de la API: captcha (RF-06), registro de eventos
(RNF-17) y validación de archivos subidos (RNF-19)."""
from captcha.helpers import captcha_image_url
from captcha.models import CaptchaStore
from django.core.cache import cache
from django.utils import timezone

from ..models import ActivityLog
from ..utils import get_client_ip

# ---------------------------------------------------------------- captcha
LOGIN_FAILS_BEFORE_CAPTCHA = 3
LOGIN_FAIL_WINDOW = 15 * 60


def new_captcha(request):
    key = CaptchaStore.generate_key()
    return {'key': key, 'image': request.build_absolute_uri(captcha_image_url(key))}


def check_captcha(key, answer):
    """Valida (y consume) un captcha. Devuelve True si la respuesta es correcta."""
    if not key or not answer:
        return False
    store = CaptchaStore.objects.filter(hashkey=key, expiration__gt=timezone.now()).first()
    if not store:
        return False
    ok = store.response == str(answer).strip().lower()
    store.delete()
    return ok


def _fail_key(identifier):
    return f'api_login_fail:{(identifier or "").strip().lower()}'


def login_needs_captcha(identifier):
    return cache.get(_fail_key(identifier), 0) >= LOGIN_FAILS_BEFORE_CAPTCHA


def register_login_failure(identifier):
    key = _fail_key(identifier)
    cache.set(key, cache.get(key, 0) + 1, LOGIN_FAIL_WINDOW)


def clear_login_failures(identifier):
    cache.delete(_fail_key(identifier))


# ---------------------------------------------------------------- eventos
def log_action(request, user, action_type, description):
    """Registra un evento relevante de seguridad, pagos o administración."""
    try:
        ActivityLog.objects.create(
            user=user, action_type=action_type, description=f'[app móvil] {description}'[:1000],
            ip_address=get_client_ip(request), user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        )
    except Exception:
        pass  # el registro nunca debe romper la operación


# ---------------------------------------------------------------- archivos
from ..utils.uploads import validate_upload  # noqa: E402,F401  (RNF-19, compartido con el web)
