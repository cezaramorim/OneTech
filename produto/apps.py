from django.apps import AppConfig

class ProdutoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'produto'

    def ready(self):
        # Importa os modelos e sinais aqui para garantir que estejam carregados
        from django.db.models.signals import post_save, post_delete, pre_delete
        from django.dispatch import receiver
        from django.db.models import Sum # Importar Sum
        from produto.models_entradas import EntradaProduto
        from .models import Produto # Importa Produto diretamente
        import produto.signals # Importa os signals para que sejam registrados

        

        # 🔁 Importa models adicionais ao inicializar o app
        import produto.models_entradas
        import produto.models_fiscais
