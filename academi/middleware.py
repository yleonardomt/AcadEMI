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
