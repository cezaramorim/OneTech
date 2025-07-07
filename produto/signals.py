# produto/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from decimal import Decimal
from .models import Produto
from .models_entradas import EntradaProduto

@receiver(post_save, sender=EntradaProduto)
def update_product_stock_on_entrada_save(sender, instance, created, **kwargs):
    print(f"DEBUG: Signal post_save para EntradaProduto (ID: {instance.pk}) acionado. Created: {created}")
    produto = instance.item_nota_fiscal.produto
    quantidade_entrada = instance.quantidade
    preco_unitario_entrada = instance.preco_unitario

    if produto.controla_estoque:
        # Garante que estamos trabalhando com os dados mais recentes do produto
        produto.refresh_from_db()
        print(f"DEBUG: Produto {produto.nome} (ID: {produto.pk}) antes do update: Estoque Total: {produto.estoque_total}, Preço Médio: {produto.preco_medio}, Preço Custo: {produto.preco_custo}")

        if created:
            # Se a EntradaProduto foi criada, adiciona ao estoque
            novo_estoque_total = produto.estoque_total + quantidade_entrada
            
            # Calcula o novo preço médio ponderado
            if novo_estoque_total > 0:
                novo_preco_medio = ((produto.preco_medio * produto.estoque_total) + \
                                    (preco_unitario_entrada * quantidade_entrada)) / novo_estoque_total
            else:
                novo_preco_medio = Decimal('0')

            produto.estoque_total = novo_estoque_total
            produto.preco_medio = novo_preco_medio
            produto.preco_custo = preco_unitario_entrada # Atualiza o preço de custo com o último preço de entrada
            print(f"DEBUG: Entrada criada. Novo Estoque Total: {novo_estoque_total}, Novo Preço Médio: {novo_preco_medio}, Novo Preço Custo: {preco_unitario_entrada}")
        else:
            # Se a EntradaProduto foi modificada, recalcula o estoque e preço médio
            # Isso é mais complexo e pode exigir o registro do valor antigo
            # Para simplificar, vamos considerar que modificações são raras e o foco é na criação/deleção
            # Uma abordagem mais robusta envolveria passar o valor antigo no signal ou recalcular tudo
            # Por enquanto, vamos apenas garantir que o estoque_atual seja recalculado
            print(f"DEBUG: Entrada modificada. Recalculando estoque e preços para {produto.nome}.")
            # Chama o método de recalcular do produto para garantir consistência
            produto.recalculate_stock_and_prices()
            return # O save será feito dentro de recalculate_stock_and_prices

        produto.save(update_fields=['estoque_total', 'preco_medio', 'preco_custo', 'estoque_atual'])
        print(f"DEBUG: Estoque do produto {produto.nome} atualizado via signal (save).")

@receiver(post_delete, sender=EntradaProduto)
def update_product_stock_on_entrada_delete(sender, instance, **kwargs):
    print(f"DEBUG: Signal post_delete para EntradaProduto (ID: {instance.pk}) acionado.")
    produto = instance.item_nota_fiscal.produto
    quantidade_entrada = instance.quantidade
    preco_unitario_entrada = instance.preco_unitario

    if produto.controla_estoque:
        # Garante que estamos trabalhando com os dados mais recentes do produto
        produto.refresh_from_db()
        print(f"DEBUG: Produto {produto.nome} (ID: {produto.pk}) antes do delete: Estoque Total: {produto.estoque_total}, Preço Médio: {produto.preco_medio}, Preço Custo: {produto.preco_custo}")

        novo_estoque_total = produto.estoque_total - quantidade_entrada
        
        # Recalcula o preço médio. Se o estoque ficar zero, o preço médio também zera.
        # Uma abordagem mais precisa para o preço médio em caso de deleção
        # exigiria um histórico de entradas para recalcular a média sem o item deletado.
        # Por simplicidade, se o estoque for zero, o preço médio será zero.
        if novo_estoque_total > 0:
            # Para um recálculo preciso do preço médio após a exclusão,
            # seria necessário somar todas as entradas restantes e seus valores.
            # Por enquanto, vamos apenas ajustar o estoque e manter o preço médio atual.
            print(f"DEBUG: Entrada deletada. Novo Estoque Total: {novo_estoque_total}. Preço médio não recalculado diretamente aqui.")
            pass 
        else:
            novo_preco_medio = Decimal('0')
            produto.preco_medio = novo_preco_medio
            produto.preco_custo = Decimal('0') # Zera o preço de custo se o estoque for zero
            print(f"DEBUG: Entrada deletada. Estoque zerado. Preço Médio e Preço Custo zerados.")

        produto.estoque_total = novo_estoque_total
        produto.save(update_fields=['estoque_total', 'preco_medio', 'preco_custo', 'estoque_atual'])
        print(f"DEBUG: Estoque do produto {produto.nome} atualizado via signal (delete).")