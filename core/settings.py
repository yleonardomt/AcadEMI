"""
Django settings for core project.
"""

from pathlib import Path
import os

from dotenv import load_dotenv

# ============================================
# CONFIGURACIÓN BASE
# ============================================
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-tu-clave-secreta-aqui')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h.strip()]


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
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'academi.middleware.EmailVerificationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
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
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'academi_db'),
        'USER': os.environ.get('DB_USER', 'academi_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}


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
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True


# ============================================
# ARCHIVOS ESTÁTICOS Y MEDIA
# ============================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

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
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# CONFIGURACIÓN SMTP DE GMAIL
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# CREDENCIALES DE GMAIL
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')  # Contraseña de aplicación (SIN ESPACIOS)

# EMAIL DE ORIGEN
DEFAULT_FROM_EMAIL = f'AcadEMI <{EMAIL_HOST_USER}>'

# URL DEL SITIO (PARA ENLACES EN CORREOS)
SITE_URL = os.environ.get('SITE_URL', 'http://127.0.0.1:8001')

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
# DESCOMENTAR PARA PRODUCCIÓN
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True


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

# Seguridad de sesión (cookies "Secure" solo tienen sentido bajo HTTPS, es decir, cuando DEBUG=False)
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# Headers de seguridad
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Tiempo límite por defecto para evaluaciones
DEFAULT_QUIZ_TIME_LIMIT = 30  # minutos
MAX_ATTEMPTS_PER_QUIZ = 3