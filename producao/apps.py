from django.apps import AppConfig


class ProducaoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'producao'

    def ready(self):
        import producao.signals
