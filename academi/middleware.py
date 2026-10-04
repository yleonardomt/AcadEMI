from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import resolve, Resolver404
from django.conf import settings


class EmailVerificationMiddleware:
    """Bloquea el acceso al resto del sitio a un usuario autenticado que
    todavía no confirmó su correo (RF-07), mandándolo a la página de
    espera en vez de dejarlo entrar directo al dashboard como antes (el
    registro solo le avisaba con un mensaje y seguía de largo). Se hace
    acá como middleware, y no como un chequeo repetido en cada vista,
    para no duplicar la misma lógica en todas las vistas protegidas."""

    EXEMPT_URL_NAMES = {'verify_pending', 'resend_verification_email', 'verify_email', 'logout', 'terms'}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if (
            user is not None and user.is_authenticated
            and not (user.is_staff or user.is_superuser or user.role == 'admin')
            and not user.email_verified
            and not request.path.startswith(settings.STATIC_URL)
            and not request.path.startswith(settings.MEDIA_URL)
            and not request.path.startswith('/admin/')
        ):
            try:
                url_name = resolve(request.path).url_name
            except Resolver404:
                url_name = None
            if url_name not in self.EXEMPT_URL_NAMES:
                return redirect('verify_pending')
        return self.get_response(request)


class UploadValidationMiddleware:
    """RNF-19: rechaza archivos con formato o tamaño no permitidos antes de que
    lleguen a las vistas (imágenes, videos, documentos y entregas de tareas).
    La API móvil valida por su cuenta, así que se omite aquí."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.method == 'POST'
            and request.content_type
            and request.content_type.startswith('multipart/')
            and not request.path.startswith(('/api/', '/admin/'))
        ):
            from .utils.uploads import FIELD_KINDS, validate_upload
            for field, kind in FIELD_KINDS.items():
                uploaded = request.FILES.get(field)
                if not uploaded:
                    continue
                problem = validate_upload(uploaded, kind)
                if problem:
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'message': problem}, status=400)
                    messages.error(request, problem)
                    return redirect(request.META.get('HTTP_REFERER') or '/')
        return self.get_response(request)


class AdminAuditMiddleware:
    """RNF-17: deja constancia de cada acción administrativa (POST exitoso sobre
    las rutas /panel/) con quién, qué y desde dónde."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = getattr(request, 'user', None)
        if (
            request.method == 'POST'
            and request.path.startswith('/panel/')
            and user is not None and user.is_authenticated and getattr(user, 'role', '') == 'admin'
            and response.status_code < 400
        ):
            from .models import ActivityLog
            from .utils import get_client_ip
            try:
                ActivityLog.objects.create(
                    user=user, action_type='other', description=f'Acción de administrador: {request.path}',
                    ip_address=get_client_ip(request), user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                )
            except Exception:
                pass
        return response
