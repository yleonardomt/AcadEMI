from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('captcha/', include('captcha.urls')),  # <--- AGREGAR ESTO
    path('api/v1/', include('academi.api.urls')),  # API JSON de la app móvil (MOVIL/)
    path('', include('academi.urls')),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
elif settings.STORAGES['default']['BACKEND'] == 'django.core.files.storage.FileSystemStorage':
    # Las imágenes incluidas en el repositorio se sirven sin publicar entregas
    # de estudiantes, certificados u otros archivos privados.
    urlpatterns += [re_path(
        r'^media/(?P<path>courses/emi-[a-z0-9-]+\.jpg)$',
        serve, {'document_root': settings.MEDIA_ROOT},
    )]

handler400 = 'core.error_views.bad_request'
handler403 = 'core.error_views.permission_denied'
handler404 = 'core.error_views.page_not_found'
handler500 = 'core.error_views.server_error'
