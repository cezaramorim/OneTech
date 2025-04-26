from django.db import models
from django.utils.timezone import now
from empresas.models import Empresa  # ou Fornecedor, dependendo do seu projeto

class CategoriaProduto(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome


class UnidadeMedida(models.Model):
    sigla = models.CharField(max_length=10, unique=True)
    descricao = models.CharField(max_length=100)

    def __str__(self):
        return self.sigla


class NCM(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    descricao = models.TextField()

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"


class Produto(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    nome = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True)

    categoria = models.ForeignKey(CategoriaProduto, on_delete=models.SET_NULL, null=True, related_name='produtos')
    unidade_medida = models.ForeignKey(UnidadeMedida, on_delete=models.SET_NULL, null=True, related_name='produtos')
    ncm = models.ForeignKey(NCM, on_delete=models.SET_NULL, null=True, blank=True, related_name='produtos')
    cfop = models.CharField(max_length=10, blank=True, null=True)

    preco_custo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    preco_medio = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    estoque_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantidade_saidas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estoque_atual = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    controla_estoque = models.BooleanField(default=True)
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateField(default=now)

    observacoes = models.TextField(blank=True, null=True)

    # 🔗 Referência ao fornecedor (emitente da NFe)
    fornecedor = models.ForeignKey(
        Empresa, on_delete=models.SET_NULL, null=True, blank=True, related_name="produtos_fornecidos",
        help_text="Empresa fornecedora vinculada via XML da nota fiscal."
    )

    # 🧾 Dados fiscais complementares
    codigo_barras = models.CharField(max_length=50, blank=True, null=True, help_text="Código de barras (EAN)")
    cst = models.CharField(max_length=5, blank=True, null=True, help_text="Código de Situação Tributária (CST/CSOSN)")
    origem_mercadoria = models.CharField(max_length=1, blank=True, null=True, help_text="Origem da mercadoria (0-8)")
    valor_unitario_comercial = models.DecimalField("Valor Unitário Comercial", max_digits=10, decimal_places=2, blank=True, null=True)


    
    # 💰 Impostos destacados na nota
    icms = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    ipi = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    pis = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cofins = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # 📦 Dados comerciais da nota
    unidade_comercial = models.CharField(max_length=10, blank=True, null=True, help_text="Unidade usada na nota (ex: UN, KG)")
    quantidade_comercial = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    codigo_produto_fornecedor = models.CharField(max_length=100, blank=True, null=True, help_text="Código interno do fornecedor (cProd)")

    # ... (métodos e __str__ permanecem iguais)


    def calcular_estoque_atual(self):
        return self.estoque_total - self.quantidade_saidas

    def save(self, *args, **kwargs):
        self.estoque_atual = self.calcular_estoque_atual()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.nome}"
