from django.apps import AppConfig


class NotaFiscalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nota_fiscal'

    def ready(self):
        import nota_fiscal.signals
