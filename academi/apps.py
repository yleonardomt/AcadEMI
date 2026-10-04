from django.apps import AppConfig


class AcademiConfig(AppConfig):
    name = 'academi'

    def ready(self):
        from . import signals  # noqa: F401  (registra el log de autenticación, RNF-17)
