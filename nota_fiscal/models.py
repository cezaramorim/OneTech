from django.db import models
from empresas.models import EmpresaAvancada

class NotaFiscal(models.Model):
    """Model para armazenar dados gerais da Nota Fiscal."""
    fornecedor = models.ForeignKey(EmpresaAvancada, on_delete=models.SET_NULL, null=True, blank=True, related_name="notas_fornecedor")
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

    def __str__(self):
        return f"Nota {self.numero} - {self.fornecedor.razao_social if self.fornecedor else 'Fornecedor Desconhecido'}"

class TransporteNotaFiscal(models.Model):
    """Model para armazenar dados do transporte da Nota Fiscal."""
    nota_fiscal = models.OneToOneField(NotaFiscal, on_delete=models.CASCADE, related_name="transporte")
    modalidade_frete = models.CharField(max_length=2, choices=[
        ('0', 'Contratação do Frete por Conta do Remetente (CIF)'),
        ('1', 'Contratação do Frete por Conta do Destinatário (FOB)'),
        ('2', 'Contratação do Frete por Conta de Terceiros'),
        ('9', 'Sem Ocorrência de Transporte')
    ], blank=True, null=True)
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
    nota_fiscal = models.ForeignKey(NotaFiscal, on_delete=models.CASCADE, related_name="duplicatas")
    numero = models.CharField(max_length=20)
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    vencimento = models.DateField()

    def __str__(self):
        return f"Duplicata {self.numero} da Nota {self.nota_fiscal.numero}"
