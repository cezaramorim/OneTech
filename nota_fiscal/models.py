from django.db import models
from django.conf import settings
from empresas.models import EmpresaAvancada
from django.utils import timezone
from django.apps import apps

class NotaFiscal(models.Model):
    # ... campos existentes ...
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="notas_criadas"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Entrada"
    )

    def __str__(self):
        return f"Nota {self.numero} – {self.fornecedor.razao_social if self.fornecedor else 'Fornecedor Desconhecido'}"

    
    fornecedor = models.ForeignKey(
        EmpresaAvancada,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="notas_fornecedor"
    )
    numero = models.CharField(max_length=20)
    natureza_operacao = models.CharField(max_length=255)
    data_emissao = models.DateField(null=True, blank=True)
    data_saida = models.DateField(null=True, blank=True)
    chave_acesso = models.CharField(max_length=50, unique=True)
    valor_total_produtos = models.DecimalField(max_digits=18, decimal_places=10, default=0)
    valor_total_nota = models.DecimalField(max_digits=18, decimal_places=10, default=0)
    valor_total_icms = models.DecimalField(max_digits=18, decimal_places=10, default=0)
    valor_total_pis = models.DecimalField(max_digits=18, decimal_places=10, default=0)
    valor_total_cofins = models.DecimalField(max_digits=18, decimal_places=10, default=0)
    valor_total_desconto = models.DecimalField(max_digits=18, decimal_places=10, default=0)
    informacoes_adicionais = models.TextField(blank=True, null=True)

    # → Campo para guardar quem criou/importou a nota
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="notas_criadas"
    )

    def __str__(self):
        return f"Nota {self.numero} - {self.fornecedor.razao_social if self.fornecedor else 'Fornecedor Desconhecido'}"


class TransporteNotaFiscal(models.Model):
    """Model para armazenar dados do transporte da Nota Fiscal."""
    nota_fiscal = models.OneToOneField(
        NotaFiscal,
        on_delete=models.CASCADE,
        related_name="transporte"
    )
    modalidade_frete = models.CharField(
        max_length=2,
        choices=[
            ('0', 'CIF'),
            ('1', 'FOB'),
            ('2', 'Terceiros'),
            ('9', 'Sem transporte')
        ],
        blank=True, null=True
    )
    transportadora_nome = models.CharField(max_length=255, blank=True, null=True)
    transportadora_cnpj = models.CharField(max_length=20, blank=True, null=True)
    placa_veiculo = models.CharField(max_length=10, blank=True, null=True)
    uf_veiculo = models.CharField(max_length=2, blank=True, null=True)
    rntc = models.CharField(max_length=20, blank=True, null=True)
    quantidade_volumes = models.PositiveIntegerField(default=0)
    especie_volumes = models.CharField(max_length=50, blank=True, null=True)
    peso_liquido = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    peso_bruto = models.DecimalField(max_digits=14, decimal_places=4, default=0)

    def __str__(self):
        return f"Transporte da Nota {self.nota_fiscal.numero}"


class DuplicataNotaFiscal(models.Model):
    """Model para armazenar parcelas (duplicatas) da Nota Fiscal."""
    nota_fiscal = models.ForeignKey(
        NotaFiscal,
        on_delete=models.CASCADE,
        related_name="duplicatas"
    )
    numero = models.CharField(max_length=20)
    valor = models.DecimalField(max_digits=18, decimal_places=10)
    vencimento = models.DateField()

    def __str__(self):
        return f"Duplicata {self.numero} da Nota {self.nota_fiscal.numero}"
    
class ItemNotaFiscal(models.Model):
    nota_fiscal = models.ForeignKey(
        'NotaFiscal',
        on_delete=models.CASCADE,
        related_name='itens'
    )
    produto = models.ForeignKey(
        'produto.produto',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='itens_nota'
    )
    codigo = models.CharField(max_length=50)
    descricao = models.CharField(max_length=255)
    ncm = models.CharField(max_length=10, blank=True, null=True)
    cfop = models.CharField(max_length=10, blank=True, null=True)
    unidade = models.CharField(max_length=10, blank=True, null=True)
    quantidade = models.DecimalField(max_digits=18, decimal_places=10, default=0)
    valor_unitario = models.DecimalField(max_digits=18, decimal_places=10, default=0)
    valor_total = models.DecimalField(max_digits=18, decimal_places=10, default=0)
    icms = models.DecimalField(max_digits=10, decimal_places=10, blank=True, null=True)
    ipi = models.DecimalField(max_digits=10, decimal_places=10, blank=True, null=True)
    desconto = models.DecimalField(max_digits=18, decimal_places=10, blank=True, null=True)

    def __str__(self):
        return f"{self.codigo} - {self.descricao} (Nota {self.nota_fiscal.numero})"

class EntradaProduto(models.Model):
    produto = models.ForeignKey('produto.Produto', on_delete=models.CASCADE)
    fornecedor = models.ForeignKey(
        EmpresaAvancada, on_delete=models.SET_NULL, null=True, blank=True
    )
    nota_fiscal = models.ForeignKey(  # ← ESSA LINHA ADICIONADA
        'NotaFiscal',
        on_delete=models.CASCADE,
        related_name='entradas_estoque',
        null=True, blank=True
    )
    quantidade = models.DecimalField(max_digits=15, decimal_places=6, default=0)
    preco_unitario = models.DecimalField(max_digits=15, decimal_places=6, default=0)
    preco_total = models.DecimalField(max_digits=15, decimal_places=6, default=0)
    numero_nota = models.CharField(max_length=50, blank=True, null=True)

    icms_valor = models.DecimalField(max_digits=15, decimal_places=6, blank=True, null=True)
    icms_aliquota = models.DecimalField(max_digits=15, decimal_places=6, blank=True, null=True)
    pis_valor = models.DecimalField(max_digits=15, decimal_places=6, blank=True, null=True)
    pis_aliquota = models.DecimalField(max_digits=15, decimal_places=6, blank=True, null=True)
    cofins_valor = models.DecimalField(max_digits=15, decimal_places=6, blank=True, null=True)
    cofins_aliquota = models.DecimalField(max_digits=15, decimal_places=6, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.produto} - {self.quantidade}"


