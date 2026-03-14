from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # Conecta sinais de autenticacao para telemetria da Central de Seguranca.
        from . import signals  # noqa: F401