"""
Django settings for core project.
"""

from pathlib import Path
import os

# ============================================
# CONFIGURACIÓN BASE
# ============================================
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-tu-clave-secreta-aqui'

DEBUG = True

ALLOWED_HOSTS = []


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
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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
CAPTCHA_CHALLENGE_FUNCT = 'captcha.helpers.math_challenge'


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
EMAIL_HOST_USER = 'yonconortorez@gmail.com'
EMAIL_HOST_PASSWORD = 'tpphpjlragfqspuu'  # Contraseña de aplicación (SIN ESPACIOS)

# EMAIL DE ORIGEN
DEFAULT_FROM_EMAIL = 'AcadEMI <yonconortorez@gmail.com>'

# URL DEL SITIO (PARA ENLACES EN CORREOS)
SITE_URL = 'http://127.0.0.1:8001'

# OPCIÓN PARA DESARROLLO (MUESTRA CORREOS EN CONSOLA)
# DESCOMENTAR PARA DESARROLLO SIN ENVIAR CORREOS REALES
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


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