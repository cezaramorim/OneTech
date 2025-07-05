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

        @receiver(post_save, sender=EntradaProduto)
        def atualizar_estoque_on_entrada_save(sender, instance, created, **kwargs):
            if instance.item_nota_fiscal and instance.item_nota_fiscal.produto:
                produto = Produto.objects.get(pk=instance.item_nota_fiscal.produto.pk)
                total_entradas = EntradaProduto.objects.filter(item_nota_fiscal__produto=produto).aggregate(Sum('quantidade'))['quantidade__sum'] or 0
                produto.estoque_total = total_entradas
                produto.estoque_atual = produto.estoque_total - produto.quantidade_saidas # Recalcula estoque_atual
                produto.save(update_fields=['estoque_total', 'estoque_atual'])

        @receiver(pre_delete, sender=EntradaProduto)
        def atualizar_estoque_on_entrada_delete(sender, instance, **kwargs):
            # Verifica se o item_nota_fiscal e o produto ainda existem antes de tentar acessá-los
            if instance.item_nota_fiscal and instance.item_nota_fiscal.produto:
                produto = Produto.objects.get(pk=instance.item_nota_fiscal.produto.pk)
                # Antes de deletar a EntradaProduto, subtrai sua quantidade do estoque total
                produto.estoque_total -= instance.quantidade
                produto.estoque_atual = produto.estoque_total - produto.quantidade_saidas
                produto.save(update_fields=['estoque_total', 'estoque_atual'])

        # 🔁 Importa models adicionais ao inicializar o app
        import produto.models_entradas
        import produto.models_fiscais
