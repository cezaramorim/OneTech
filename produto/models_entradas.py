from django.db import models
from django.utils.timezone import now
from produto.models import Produto
from empresas.models import EmpresaAvancada

class EntradaProduto(models.Model):
    nota_fiscal = models.ForeignKey('nota_fiscal.NotaFiscal', on_delete=models.CASCADE, related_name='entradas_produto', null=True, blank=True)
    item_nota_fiscal = models.ForeignKey('nota_fiscal.ItemNotaFiscal', on_delete=models.CASCADE, related_name='entradas_produto', null=True, blank=True)
    fornecedor = models.ForeignKey('empresas.EmpresaAvancada', on_delete=models.CASCADE, related_name='entradas_produto', null=True, blank=True)
    quantidade = models.DecimalField(max_digits=15, decimal_places=6)
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
        return f"Entrada {self.item_nota_fiscal.produto.nome} - {self.quantidade} unid."

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
