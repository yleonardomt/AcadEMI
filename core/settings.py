"""
Django settings for core project.
"""

from pathlib import Path
import os
from urllib.parse import parse_qsl, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

from dotenv import load_dotenv

# ============================================
# CONFIGURACIÓN BASE
# ============================================
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')

def env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(name):
    return [item.strip() for item in os.environ.get(name, '').split(',') if item.strip()]


SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-tu-clave-secreta-aqui')

DEBUG = env_bool('DEBUG')
DEMO_CHECKOUT = env_bool('DEMO_CHECKOUT')

RENDER_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '').strip()
RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL', '').strip().rstrip('/')
ON_RENDER = bool(os.environ.get('RENDER'))

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS')
if RENDER_HOSTNAME and RENDER_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_HOSTNAME)
SITE_URL = os.environ.get('SITE_URL', '').strip().rstrip('/') or RENDER_URL
if not SITE_URL and RENDER_HOSTNAME:
    SITE_URL = f'https://{RENDER_HOSTNAME}'
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS')
if SITE_URL:
    parsed_site = urlparse(SITE_URL)
    if (parsed_site.scheme not in ('http', 'https') or not parsed_site.hostname
            or parsed_site.path or parsed_site.query or parsed_site.fragment
            or parsed_site.username or parsed_site.password):
        raise ImproperlyConfigured('SITE_URL debe ser una URL de origen válida, sin ruta ni parámetros.')
    origin = f'{parsed_site.scheme}://{parsed_site.netloc}'
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

if not DEBUG:
    if SECRET_KEY.startswith('django-insecure-') or SECRET_KEY == 'change-me-to-a-random-secret-key':
        raise ImproperlyConfigured('Define una SECRET_KEY única en las variables de entorno antes de usar DEBUG=False.')
    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured('Define ALLOWED_HOSTS con la IP o dominio público antes de usar DEBUG=False.')
    if '*' in ALLOWED_HOSTS:
        raise ImproperlyConfigured('ALLOWED_HOSTS no puede contener * con DEBUG=False.')
    if not SITE_URL:
        raise ImproperlyConfigured('Define SITE_URL con la URL pública antes de usar DEBUG=False.')


# ============================================
# APLICACIONES INSTALADAS
# ============================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'captcha',  # django-simple-captcha
   
    'academi',
]


# ============================================
# MIDDLEWARE
# ============================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'academi.middleware.EmailVerificationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'academi.middleware.UploadValidationMiddleware',
    'academi.middleware.AdminAuditMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ============================================
# BACKENDS DE AUTENTICACIÓN
# ============================================
# UsernameOrEmailBackend primero (permite loguearse con username o email,
# tal como promete el placeholder del login); ModelBackend queda como
# respaldo estándar de Django.
AUTHENTICATION_BACKENDS = [
    'academi.auth_backends.UsernameOrEmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]


# ============================================
# URLS Y TEMPLATES
# ============================================
ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'academi.context_processors.header_counters',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# ============================================
# BASE DE DATOS
# ============================================
DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()
if DATABASE_URL:
    database = urlparse(DATABASE_URL)
    if (database.scheme not in ('postgres', 'postgresql') or not database.hostname
            or not database.path.strip('/') or database.fragment):
        raise ImproperlyConfigured('DATABASE_URL debe ser una URL PostgreSQL válida.')
    try:
        database_port = database.port or 5432
    except ValueError as exc:
        raise ImproperlyConfigured('DATABASE_URL tiene un puerto inválido.') from exc
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': unquote(database.path.lstrip('/')),
        'USER': unquote(database.username or ''),
        'PASSWORD': unquote(database.password or ''),
        'HOST': database.hostname,
        'PORT': str(database_port),
        'OPTIONS': dict(parse_qsl(database.query, keep_blank_values=True)),
    }}
else:
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'academi_db'),
        'USER': os.environ.get('DB_USER', 'academi_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }}


# ============================================
# VALIDACIÓN DE CONTRASEÑAS
# ============================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ============================================
# IDIOMA Y ZONA HORARIA
# ============================================
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/La_Paz'
USE_I18N = True
USE_TZ = True


# ============================================
# ARCHIVOS ESTÁTICOS Y MEDIA
# ============================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

# Archivos de cursos, entregas y certificados. Render Free pierde los archivos
# locales al reiniciar; un bucket S3 compatible permite conservarlos.
S3_ENDPOINT = os.environ.get('AWS_ENDPOINT_URL_S3', '').strip()
S3_BUCKET = os.environ.get('AWS_STORAGE_BUCKET_NAME', '').strip()
S3_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID', '').strip()
S3_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '').strip()
if any((S3_ENDPOINT, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY)):
    if not all((S3_ENDPOINT, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY)):
        raise ImproperlyConfigured('Completa AWS_ENDPOINT_URL_S3, AWS_STORAGE_BUCKET_NAME, AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY.')
    STORAGES['default'] = {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            'endpoint_url': S3_ENDPOINT,
            'bucket_name': S3_BUCKET,
            'access_key': S3_ACCESS_KEY,
            'secret_key': S3_SECRET_KEY,
            'region_name': os.environ.get('AWS_REGION', 'us-east-2'),
            'addressing_style': 'path',
            'signature_version': 's3v4',
            'querystring_auth': True,
            'default_acl': None,
            'file_overwrite': False,
        },
    }

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ============================================
# MODELO DE USUARIO PERSONALIZADO
# ============================================
AUTH_USER_MODEL = 'academi.User'


# ============================================
# CONFIGURACIÓN DE CAPTCHA (django-simple-captcha)
# ============================================
CAPTCHA_CHALLENGE_FUNCT = 'captcha.helpers.random_char_challenge'
CAPTCHA_IMAGE_SIZE = (200, 60)  # Ancho, Alto
CAPTCHA_FONT_SIZE = 40
CAPTCHA_BACKGROUND_COLOR = '#ffffff'  # Fondo blanco
CAPTCHA_FOREGROUND_COLOR = '#2d3748'  # Color de texto (gris oscuro)
CAPTCHA_LENGTH = 3


# ============================================
# CONFIGURACIÓN DE GOOGLE reCAPTCHA
# ============================================
# OBTENER DE: https://www.google.com/recaptcha/admin/create
# Claves de prueba (para desarrollo)
RECAPTCHA_PUBLIC_KEY = '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'
RECAPTCHA_PRIVATE_KEY = '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe'

# Para producción, usar claves reales
# RECAPTCHA_PUBLIC_KEY = 'TU_SITE_KEY_REAL'
# RECAPTCHA_PRIVATE_KEY = 'TU_SECRET_KEY_REAL'


# ============================================
# CONFIGURACIÓN DE EMAIL (GMAIL)
# ============================================
# BACKEND DE EMAIL
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')

# CONFIGURACIÓN SMTP DE GMAIL
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)

# CREDENCIALES DE GMAIL
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')  # Contraseña de aplicación (SIN ESPACIOS)

# EMAIL DE ORIGEN
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', f'AcadEMI <{EMAIL_HOST_USER}>')

# URL DEL SITIO (PARA ENLACES EN CORREOS)
# SITE_URL se define arriba y sirve también para CSRF y los enlaces de correo.

# OPCIÓN PARA DESARROLLO (MUESTRA CORREOS EN CONSOLA)
# DESCOMENTAR PARA DESARROLLO SIN ENVIAR CORREOS REALES
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ============================================
# ASISTENTE VIRTUAL CON IA (RF-77 al RF-82)
# ============================================
# Clave de Gemini (https://aistudio.google.com/apikey) — capa gratuita,
# no pide tarjeta. Se usa directo (no vía OpenRouter) para no depender
# de su pool gratuito compartido, que fue devolviendo 404 (modelo
# retirado), 429 (rate-limit) o 502 (proveedor saturado) según el
# modelo probado. Si se deja vacía, el chatbot sigue funcionando con la
# base de conocimiento propia (academi.models.ChatKnowledgeBase /
# ChatIntent) en vez de generar respuestas con IA. Ver README para cómo
# obtener la clave.
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-3.5-flash-lite')


# ============================================
# CONFIGURACIÓN DE SEGURIDAD PARA PRODUCCIÓN
# ============================================
# Render publica el servicio por HTTPS. En un VPS por HTTP, configurar
# FORCE_HTTPS=False y BEHIND_PROXY según el proxy utilizado.
FORCE_HTTPS = env_bool('FORCE_HTTPS', ON_RENDER)
SECURE_SSL_REDIRECT = FORCE_HTTPS
SESSION_COOKIE_SECURE = FORCE_HTTPS
CSRF_COOKIE_SECURE = FORCE_HTTPS
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '3600')) if FORCE_HTTPS else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
if FORCE_HTTPS:
    if SITE_URL and urlparse(SITE_URL).scheme != 'https':
        raise ImproperlyConfigured('Con FORCE_HTTPS=True, SITE_URL debe empezar por https://.')
if env_bool('BEHIND_PROXY', ON_RENDER):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# ============================================
# CONFIGURACIÓN DE SESIÓN
# ============================================
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 horas
SESSION_COOKIE_NAME = 'academi_session'


# ============================================
# LOGIN Y LOGOUT
# ============================================
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

# ============================================
# CLAVE POR DEFECTO
# ============================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================
# SEGURIDAD PARA CUESTIONARIOS
# ============================================

# Rate limiting para prevenir ataques
RATELIMIT_VIEW = 'django_ratelimit.views.ratelimited'

# CSP (Content Security Policy) - Prevenir inyecciones
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FRAME_SRC = ("'self'", "https://www.youtube.com", "https://player.vimeo.com")
CSP_CONNECT_SRC = ("'self'",)

# Las cookies Secure solo funcionan cuando el navegador accede por HTTPS.
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# Headers de seguridad
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Tiempo límite por defecto para evaluaciones
DEFAULT_QUIZ_TIME_LIMIT = 30  # minutos
MAX_ATTEMPTS_PER_QUIZ = 3
