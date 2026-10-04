import json
from functools import wraps

from django.core import signing
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ..models import User

TOKEN_SALT = 'academi.api.token'
TOKEN_MAX_AGE = 60 * 60 * 24 * 7  # 7 días (RNF-07: las sesiones expiran)

# Endpoints que un usuario con el correo sin verificar sí puede usar
# (igual que EmailVerificationMiddleware en el sitio web).
UNVERIFIED_ALLOWED = {'me', 'resend_verification', 'logout'}


def make_token(user):
    """Token firmado y con caducidad. Lleva un fragmento del hash de la
    contraseña para que cambiarla invalide los tokens anteriores."""
    return signing.dumps({'uid': user.pk, 'pw': user.password[-12:]}, salt=TOKEN_SALT)


def user_from_token(token):
    try:
        data = signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)
        user = User.objects.get(pk=data['uid'], is_active=True)
    except (signing.BadSignature, User.DoesNotExist, KeyError):
        return None
    if user.password[-12:] != data.get('pw'):
        return None
    return user


def error(message, status=400, code=None, **extra):
    payload = {'success': False, 'message': message}
    if code:
        payload['code'] = code
    payload.update(extra)
    return JsonResponse(payload, status=status)


def ok(**data):
    return JsonResponse({'success': True, **data})


def parse_body(request):
    """JSON o formulario (multipart/urlencoded) → dict plano."""
    if request.content_type and 'json' in request.content_type:
        try:
            return json.loads(request.body or b'{}')
        except json.JSONDecodeError:
            return {}
    return request.POST.dict()


def api_view(methods=('GET',), auth='required', roles=None, name=None):
    """auth: 'required' | 'optional' | 'none'. roles: tupla de roles
    permitidos (None = cualquiera)."""
    methods = tuple(m.upper() for m in methods)

    def decorator(view):
        view_name = name or view.__name__

        @csrf_exempt
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if request.method not in methods:
                return error('Método no permitido', 405)

            user = None
            header = request.META.get('HTTP_AUTHORIZATION', '')
            if header.startswith('Bearer '):
                user = user_from_token(header[7:].strip())

            request.api_user = user
            if auth == 'required' and user is None:
                return error('Sesión no válida o expirada', 401, code='UNAUTHENTICATED')

            if user is not None:
                request.user = user
                exempt = user.is_staff or user.is_superuser or user.role == 'admin'
                if not exempt and not user.email_verified and view_name not in UNVERIFIED_ALLOWED:
                    return error('Verifica tu correo electrónico para continuar.', 403, code='EMAIL_NOT_VERIFIED')
                if roles and user.role not in roles:
                    return error('No tienes permisos para esta acción.', 403, code='FORBIDDEN')

            return view(request, *args, **kwargs)

        return wrapper
    return decorator
