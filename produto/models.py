from django.db import models
from django.db.models import Sum
from django.utils.timezone import now
from empresas.models import EmpresaAvancada
from .models_fiscais import DetalhesFiscaisProduto

# 📦 Categoria de Produtos
class CategoriaProduto(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome


# 📐 Unidade de Medida (UN, KG, CX, etc.)
class UnidadeMedida(models.Model):
    sigla = models.CharField(max_length=10, unique=True)
    descricao = models.CharField(max_length=100)

    def __str__(self):
        return self.sigla


# 📚 Tabela de NCMs
class NCM(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    descricao = models.TextField()

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"


# 🛒 Produto principal — agora usado também como item da nota
class Produto(models.Model):
    # 🔑 Identificação
    codigo = models.CharField(max_length=50, unique=True)
    nome = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True)

    # 📂 Classificações
    categoria = models.ForeignKey(CategoriaProduto, on_delete=models.SET_NULL, null=True, related_name='produtos')
    unidade_medida_interna = models.ForeignKey(UnidadeMedida, on_delete=models.SET_NULL, null=True, blank=True, related_name='produtos', help_text="Unidade de medida para controle interno de estoque.")
    
    TIPOS_PRODUTO = [
        ('Produto', 'Produto'),
        ('Insumo', 'Insumo'),
        ('Matéria-prima', 'Matéria-prima'),
    ]

    tipo = models.CharField(
        max_length=30,
        choices=TIPOS_PRODUTO,
        default='Produto',
        help_text="Classificação do produto para fins operacionais."
    )


    # 💰 Preços
    preco_custo = models.DecimalField(max_digits=18, decimal_places=10, default=0)
    preco_venda = models.DecimalField(max_digits=18, decimal_places=10, default=0)
    preco_medio = models.DecimalField(max_digits=18, decimal_places=10, default=0)

    # 📦 Estoque
    estoque_total = models.DecimalField(max_digits=18, decimal_places=10, default=0)
    quantidade_saidas = models.DecimalField(max_digits=18, decimal_places=10, default=0)
    estoque_atual = models.DecimalField(max_digits=18, decimal_places=10, default=0)

    controla_estoque = models.BooleanField(default=True)
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateField(default=now)

    # 🧾 Dados fiscais complementares
    codigo_barras = models.CharField(max_length=50, blank=True, null=True, help_text="Código de barras (EAN)")
    
    # 📝 Observações
    observacoes = models.TextField(blank=True, null=True)

    # 🔗 Fornecedor
    fornecedor = models.ForeignKey(
        EmpresaAvancada,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="produtos_fornecidos",
        help_text="Empresa fornecedora vinculada via XML da nota fiscal."
    )

    # 🧾 Nota fiscal de origem (para importação XML)
    nota_fiscal = models.ForeignKey(
        'nota_fiscal.NotaFiscal',  # ← referência por string evita importações circulares
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='produtos',
        help_text="Nota fiscal à qual este produto está vinculado (caso importado do XML)"
    )

def calcular_estoque_atual(self):
    return self.estoque_total - self.quantidade_saidas

    

def save(self, *args, **kwargs):
    self.estoque_atual = self.calcular_estoque_atual()
    super().save(*args, **kwargs)

def __str__(self):
    return f"{self.codigo} - {self.nome}"


# 🔄 Fator de Conversão de Unidades por Fornecedor
class FatorConversaoFornecedor(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name="fatores_conversao")
    fornecedor = models.ForeignKey(EmpresaAvancada, on_delete=models.CASCADE, related_name="fatores_conversao")
    unidade_fornecedor = models.CharField(max_length=10, help_text="Unidade de medida usada pelo fornecedor (ex: CX, FARDO)")
    fator_conversao = models.DecimalField(
        max_digits=18, 
        decimal_places=10, 
        default=1,
        help_text="Quantas unidades internas correspondem a uma unidade do fornecedor. Ex: Se a unidade do fornecedor é 'CX' com 12 itens, o fator é 12."
    )

    class Meta:
        unique_together = ('produto', 'fornecedor', 'unidade_fornecedor')
        verbose_name = "Fator de Conversão por Fornecedor"
        verbose_name_plural = "Fatores de Conversão por Fornecedor"

    def __str__(self):
        return f"{self.produto.nome} ({self.fornecedor.nome_fantasia}): 1 {self.unidade_fornecedor} = {self.fator_conversao} unidades internas"
