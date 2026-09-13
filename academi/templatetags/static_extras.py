import os

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def static_v(path):
    """
    Igual que {% static %}, pero agrega ?v=<fecha de modificación>
    al final para que el navegador no siga usando una copia en caché
    de un CSS/JS después de editarlo (sin esto, algunos navegadores
    tardan en notar los cambios hasta un refresco forzado).
    """
    url = static(path)
    for static_dir in settings.STATICFILES_DIRS:
        file_path = os.path.join(static_dir, path)
        if os.path.exists(file_path):
            return f"{url}?v={int(os.path.getmtime(file_path))}"
    return url
