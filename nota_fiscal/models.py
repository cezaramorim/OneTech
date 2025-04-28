from django.db import models
from django.conf import settings
from empresas.models import EmpresaAvancada
from django.utils import timezone

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
    valor_total_produtos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor_total_nota = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor_total_icms = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor_total_pis = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor_total_cofins = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor_total_desconto = models.DecimalField(max_digits=14, decimal_places=2, default=0)
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
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    vencimento = models.DateField()

    def __str__(self):
        return f"Duplicata {self.numero} da Nota {self.nota_fiscal.numero}"
