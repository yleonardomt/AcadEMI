"""Respuestas de error claras para la web y la API cuando DEBUG=False."""

from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template


def _response(request, status, template, message):
    if request.path.startswith('/api/'):
        return JsonResponse({'success': False, 'message': message}, status=status)
    # Una página de error debe poder mostrarse incluso si la base de datos
    # falló; renderizar sin request evita context processors que la consulten.
    return HttpResponse(get_template(template).render(), status=status)


def bad_request(request, exception):
    return _response(request, 400, '400.html', 'Solicitud inválida.')


def permission_denied(request, exception):
    return _response(request, 403, '403.html', 'No tienes permiso para acceder a esta página.')


def page_not_found(request, exception):
    return _response(request, 404, '404.html', 'Página no encontrada.')


def server_error(request):
    return _response(request, 500, '500.html', 'Ocurrió un error del servidor.')
