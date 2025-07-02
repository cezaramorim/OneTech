from django.db import models
from django.conf import settings
from empresas.models import EmpresaAvancada # Certifique-se de que este caminho está correto
from django.utils import timezone
from django.apps import apps # Não é estritamente necessário para este arquivo, mas não atrapalha

class NotaFiscal(models.Model):
    # Campos de controle/auditoria
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

    # RELACIONAMENTOS ESSENCIAIS PARA NF-e (Emitente e Destinatário)
    emitente = models.ForeignKey(
        EmpresaAvancada,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="notas_emitidas",
        verbose_name="Emitente (Fornecedor)"
    )
    destinatario = models.ForeignKey(
        EmpresaAvancada,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="notas_recebidas",
        verbose_name="Destinatário"
    )

    # Campos de cabeçalho da Nota Fiscal
    numero = models.CharField(max_length=20, verbose_name="Número da NF")
    natureza_operacao = models.CharField(max_length=255, verbose_name="Natureza da Operação")
    data_emissao = models.DateField(null=True, blank=True, verbose_name="Data de Emissão")
    data_saida = models.DateField(null=True, blank=True, verbose_name="Data de Saída/Entrada")
    chave_acesso = models.CharField(max_length=44, unique=True, verbose_name="Chave de Acesso") # Chave da NF-e tem 44 dígitos
    
    raw_payload = models.JSONField(
        verbose_name='Payload bruto da importação',
        help_text='JSON puro extraído do infNFe',
        null=True,
        blank=True,
    )

    # Valores totais da Nota Fiscal (decimal_places ajustados para 4)
    valor_total_produtos = models.DecimalField(max_digits=15, decimal_places=4, default=0, verbose_name="Valor Total dos Produtos")
    valor_total_nota = models.DecimalField(max_digits=15, decimal_places=4, default=0, verbose_name="Valor Total da Nota")
    valor_total_icms = models.DecimalField(max_digits=15, decimal_places=4, default=0, verbose_name="Valor Total ICMS")
    valor_total_pis = models.DecimalField(max_digits=15, decimal_places=4, default=0, verbose_name="Valor Total PIS")
    valor_total_cofins = models.DecimalField(max_digits=15, decimal_places=4, default=0, verbose_name="Valor Total COFINS")
    valor_total_desconto = models.DecimalField(max_digits=15, decimal_places=4, default=0, verbose_name="Valor Total Desconto")
    
    informacoes_adicionais = models.TextField(blank=True, null=True, verbose_name="Informações Adicionais")

    class Meta:
        verbose_name = "Nota Fiscal"
        verbose_name_plural = "Notas Fiscais"
        ordering = ['-data_emissao', '-numero'] # Ordenação padrão

    def __str__(self):
        return f"Nota {self.numero} – {self.emitente.razao_social if self.emitente else 'Emitente Desconhecido'} ({self.chave_acesso})"

    # Se você removeu o campo 'fornecedor', ajuste seu código aqui ou em qualquer outro lugar que o use.
    # Se você pretende manter 'fornecedor' para outro propósito, o views.py atual não o popula.

class TransporteNotaFiscal(models.Model):
    """Model para armazenar dados do transporte da Nota Fiscal."""
    nota_fiscal = models.OneToOneField(
        NotaFiscal,
        on_delete=models.CASCADE,
        related_name="transporte",
        verbose_name="Nota Fiscal"
    )
    modalidade_frete = models.CharField(
        max_length=2,
        choices=[
            ('0', 'Contratação do Frete por conta do Remetente (CIF)'),
            ('1', 'Contratação do Frete por conta do Destinatário (FOB)'),
            ('2', 'Contratação do Frete por conta de Terceiros'),
            ('3', 'Transporte Próprio por conta do Remetente'),
            ('4', 'Transporte Próprio por conta do Destinatário'),
            ('9', 'Sem Ocorrência de Transporte')
        ],
        blank=True, null=True,
        verbose_name="Modalidade do Frete"
    )
    transportadora_nome = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nome Transportadora")
    transportadora_cnpj = models.CharField(max_length=20, blank=True, null=True, verbose_name="CNPJ Transportadora")
    placa_veiculo = models.CharField(max_length=10, blank=True, null=True, verbose_name="Placa do Veículo")
    uf_veiculo = models.CharField(max_length=2, blank=True, null=True, verbose_name="UF do Veículo")
    rntc = models.CharField(max_length=20, blank=True, null=True, verbose_name="RNTC")
    quantidade_volumes = models.PositiveIntegerField(default=0, verbose_name="Quantidade de Volumes")
    especie_volumes = models.CharField(max_length=50, blank=True, null=True, verbose_name="Espécie dos Volumes")
    peso_liquido = models.DecimalField(max_digits=14, decimal_places=4, default=0, verbose_name="Peso Líquido (kg)")
    peso_bruto = models.DecimalField(max_digits=14, decimal_places=4, default=0, verbose_name="Peso Bruto (kg)")

    class Meta:
        verbose_name = "Transporte da Nota Fiscal"
        verbose_name_plural = "Transportes da Nota Fiscal"

    def __str__(self):
        return f"Transporte da Nota {self.nota_fiscal.numero}"


class DuplicataNotaFiscal(models.Model):
    """Model para armazenar parcelas (duplicatas) da Nota Fiscal."""
    nota_fiscal = models.ForeignKey(
        NotaFiscal,
        on_delete=models.CASCADE,
        related_name="duplicatas",
        verbose_name="Nota Fiscal"
    )
    numero = models.CharField(max_length=20, verbose_name="Número da Duplicata")
    valor = models.DecimalField(max_digits=15, decimal_places=4, verbose_name="Valor")
    vencimento = models.DateField(verbose_name="Data de Vencimento")

    class Meta:
        verbose_name = "Duplicata da Nota Fiscal"
        verbose_name_plural = "Duplicatas da Nota Fiscal"
        unique_together = ('nota_fiscal', 'numero') # Garante que não há duplicatas com o mesmo número para a mesma NF

    def __str__(self):
        return f"Duplicata {self.numero} da Nota {self.nota_fiscal.numero}"
    
class ItemNotaFiscal(models.Model):
    nota_fiscal = models.ForeignKey(
        'NotaFiscal',
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name="Nota Fiscal"
    )
    produto = models.ForeignKey(
        'produto.Produto', # String para evitar dependência circular se 'produto' importa 'nota_fiscal'
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='itens_nota',
        verbose_name="Produto"
    )
    codigo = models.CharField(max_length=50, verbose_name="Código do Produto")
    descricao = models.CharField(max_length=255, verbose_name="Descrição do Produto")
    ncm = models.CharField(max_length=10, blank=True, null=True, verbose_name="NCM")
    cfop = models.CharField(max_length=10, blank=True, null=True, verbose_name="CFOP")
    unidade = models.CharField(max_length=10, blank=True, null=True, verbose_name="Unidade Comercial")
    quantidade = models.DecimalField(max_digits=15, decimal_places=6, default=0, verbose_name="Quantidade")
    valor_unitario = models.DecimalField(max_digits=15, decimal_places=6, default=0, verbose_name="Valor Unitário")
    valor_total = models.DecimalField(max_digits=15, decimal_places=6, default=0, verbose_name="Valor Total")
    icms = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True, verbose_name="Valor ICMS")
    ipi = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True, verbose_name="Valor IPI")
    pis = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True, verbose_name="Valor PIS")
    cofins = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True, verbose_name="Valor COFINS")
    desconto = models.DecimalField(max_digits=15, decimal_places=6, blank=True, null=True, verbose_name="Valor Desconto")

    class Meta:
        verbose_name = "Item da Nota Fiscal"
        verbose_name_plural = "Itens da Nota Fiscal"
        unique_together = ('nota_fiscal', 'codigo') # Garante que não há itens com o mesmo código para a mesma NF

    def __str__(self):
        return f"{self.codigo} - {self.descricao} (Nota {self.nota_fiscal.numero})"

