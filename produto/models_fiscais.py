from django.db import models

class DetalhesFiscaisProduto(models.Model):
    produto = models.OneToOneField(
        'produto.Produto',
        on_delete=models.CASCADE,
        related_name='detalhes_fiscais'
    )
    cst = models.CharField(max_length=5, blank=True, null=True, help_text="Código de Situação Tributária (CST/CSOSN)")
    origem_mercadoria = models.CharField(max_length=1, blank=True, null=True, help_text="Origem da mercadoria (0-8)")
    valor_unitario_comercial = models.DecimalField("Valor Unitário Comercial", max_digits=18, decimal_places=10, blank=True, null=True)
    icms = models.DecimalField(max_digits=18, decimal_places=10, blank=True, null=True)
    ipi = models.DecimalField(max_digits=18, decimal_places=10, blank=True, null=True)
    pis = models.DecimalField(max_digits=18, decimal_places=10, blank=True, null=True)
    cofins = models.DecimalField(max_digits=18, decimal_places=10, blank=True, null=True)
    unidade_comercial = models.CharField(max_length=10, blank=True, null=True, help_text="Unidade usada na nota (ex: UN, KG)")
    quantidade_comercial = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    codigo_produto_fornecedor = models.CharField(max_length=100, blank=True, null=True, help_text="Código interno do fornecedor (cProd)")

    def __str__(self):
        return f"Detalhes Fiscais de {self.produto.nome}"
