"""Crea una cuenta administradora inicial solo cuando aún no existe."""

import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from academi.models import User  # noqa: E402

username = os.environ.get('ADMIN_USERNAME', '').strip()
email = os.environ.get('ADMIN_EMAIL', '').strip()
password = os.environ.get('ADMIN_PASSWORD', '')

if not any((username, email, password)):
    print('Cuenta administradora inicial: pendiente de configurar ADMIN_USERNAME, ADMIN_EMAIL y ADMIN_PASSWORD.')
elif not all((username, email, password)):
    raise SystemExit('Completa ADMIN_USERNAME, ADMIN_EMAIL y ADMIN_PASSWORD o deja las tres vacías.')
elif User.objects.filter(username=username).exists():
    print('La cuenta administradora inicial ya existe; no se cambia su contraseña.')
elif User.objects.filter(email__iexact=email).exists():
    raise SystemExit('ADMIN_EMAIL ya pertenece a otra cuenta.')
else:
    User.objects.create_superuser(
        username=username, email=email, password=password,
        role='admin', email_verified=True,
    )
    print('Cuenta administradora inicial creada.')
