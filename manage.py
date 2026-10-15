#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
        from django.core.management.commands.runserver import Command as Runserver
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # El sitio corre en el puerto 80 (http://127.0.0.1), así que `runserver`
    # sin argumentos ya escucha ahí. En Linux/WSL2 abrir el 80 requiere
    # `net.ipv4.ip_unprivileged_port_start=0` (ver README).
    Runserver.default_port = '80'
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
