from django.apps import AppConfig

class ProdutoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'produto'

    def ready(self):
        # 🔁 Importa models adicionais ao inicializar o app
        import produto.models_entradas
