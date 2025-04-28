from django.db import models
from django.utils.timezone import now
from produto.models import Produto
from empresas.models import EmpresaAvancada

class EntradaProduto(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name="entradas")
    fornecedor = models.ForeignKey(EmpresaAvancada, on_delete=models.SET_NULL, null=True, blank=True, related_name="entradas_fornecedor")
    quantidade = models.DecimalField(max_digits=18, decimal_places=10)
    preco_unitario = models.DecimalField(max_digits=18, decimal_places=10)
    preco_total = models.DecimalField(max_digits=18, decimal_places=10)
    numero_nota = models.CharField(max_length=50)
    data_entrada = models.DateField(default=now)
    # 🔥 NOVOS CAMPOS para impostos
    icms_valor = models.DecimalField(max_digits=18, decimal_places=10, default=0)
    icms_aliquota = models.DecimalField(max_digits=18, decimal_places=10, default=0)
    pis_valor = models.DecimalField(max_digits=18, decimal_places=10, default=0)
    pis_aliquota = models.DecimalField(max_digits=18, decimal_places=10, default=0)
    cofins_valor = models.DecimalField(max_digits=18, decimal_places=10, default=0)
    cofins_aliquota = models.DecimalField(max_digits=18, decimal_places=10, default=0)

    def __str__(self):
        return f"Entrada {self.produto.nome} - {self.quantidade} unid."

    def save(self, *args, **kwargs):
        # Atualiza o estoque e custo médio do Produto
        if not self.pk:  # Se é uma entrada nova
            produto = self.produto
            estoque_antigo = produto.estoque_total
            custo_antigo = produto.preco_custo

            estoque_novo = estoque_antigo + self.quantidade

            if estoque_novo > 0:
                custo_medio = ((estoque_antigo * custo_antigo) + (self.quantidade * self.preco_unitario)) / estoque_novo
            else:
                custo_medio = self.preco_unitario  # Se estoque era 0

            produto.estoque_total = estoque_novo
            produto.preco_custo = custo_medio
            produto.save()

        super().save(*args, **kwargs)
