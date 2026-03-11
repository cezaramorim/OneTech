from django.db import models
from django.conf import settings
from empresas.models import Empresa
from control.models import Emitente
from django.utils import timezone
from django.apps import apps
from fiscal.models import CST, CSOSN # Nova importaÃ§Ã£o
from produto.ncm_utils import normalizar_codigo_ncm

class NotaFiscal(models.Model):
    """Modelo para armazenar informaÃ§Ãµes de Notas Fiscais, tanto de entrada quanto de saÃ­da.
    Inclui dados do cabeÃ§alho, totais de impostos e status de comunicaÃ§Ã£o com a SEFAZ (futuro).
    """
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

    # --- RELACIONAMENTOS ---
    # Para NOTAS DE SAÃDA (nÃ³s emitimos)
    emitente_proprio = models.ForeignKey(
        Emitente,
        on_delete=models.PROTECT, # Impede a exclusÃ£o de um emitente que jÃ¡ emitiu notas
        null=True, blank=True,
        related_name="notas_proprias_emitidas",
        verbose_name="Nosso Emitente (Matriz/Filial)"
    )

    # Para NOTAS DE ENTRADA (recebemos de terceiros)
    emitente = models.ForeignKey(
        Empresa,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="notas_emitidas_por_terceiros",
        verbose_name="Emitente (Fornecedor)"
    )
    
    # Para AMBOS os casos
    destinatario = models.ForeignKey(
        Empresa,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="notas_recebidas",
        verbose_name="DestinatÃ¡rio (Cliente)"
    )

    # Campos de cabeÃ§alho da Nota Fiscal
    numero = models.CharField(max_length=20, verbose_name="NÃºmero da NF")
    natureza_operacao = models.CharField(max_length=255, verbose_name="Natureza da OperaÃ§Ã£o")
    data_emissao = models.DateField(null=True, blank=True, verbose_name="Data de EmissÃ£o")
    data_saida = models.DateField(null=True, blank=True, verbose_name="Data de SaÃ­da/Entrada")
    chave_acesso = models.CharField(max_length=44, unique=True, verbose_name="Chave de Acesso") # Chave da NF-e tem 44 dÃ­gitos
    
    raw_payload = models.JSONField(
        verbose_name='Payload bruto da importaÃ§Ã£o',
        help_text='JSON puro extraÃ­do do infNFe',
        null=True,
        blank=True,
    )

    

    # Novos campos para detalhes da NF-e
    tipo_operacao = models.CharField(
        max_length=1,
        choices=[('0', 'Entrada'), ('1', 'Saida')],
        blank=True, null=True,
        verbose_name="Tipo de OperaÃ§Ã£o"
    )
    finalidade_emissao = models.CharField(
        max_length=1,
        choices=[
            ('1', 'NF-e normal'),
            ('2', 'NF-e complementar'),
            ('3', 'NF-e de ajuste'),
            ('4', 'DevoluÃ§Ã£o de mercadoria'),
        ],
        blank=True, null=True,
        verbose_name="Finalidade da EmissÃ£o"
    )
    modelo_documento = models.CharField(
        max_length=2,
        choices=[('55', 'NF-e'), ('65', 'NFC-e')],
        blank=True, null=True,
        verbose_name="Modelo do Documento Fiscal"
    )
    serie = models.CharField(max_length=5, blank=True, null=True, verbose_name="SÃ©rie da NF")
    ambiente = models.CharField(
        max_length=1,
        choices=[('1', 'ProduÃ§Ã£o'), ('2', 'HomologaÃ§Ã£o')],
        blank=True, null=True,
        verbose_name="Ambiente de EmissÃ£o"
    )
    protocolo_autorizacao = models.CharField(max_length=15, blank=True, null=True, verbose_name="Protocolo de AutorizaÃ§Ã£o")
    data_autorizacao = models.DateTimeField(blank=True, null=True, verbose_name="Data/Hora AutorizaÃ§Ã£o")
    status_sefaz = models.CharField(max_length=50, blank=True, null=True, verbose_name="Status SEFAZ")
    motivo_status_sefaz = models.TextField(blank=True, null=True, verbose_name="Motivo Status SEFAZ")
    id_servico_terceiro = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID ServiÃ§o Terceiro")

    # Valores totais da Nota Fiscal (decimal_places ajustados para 4)
    valor_total_produtos = models.DecimalField(max_digits=15, decimal_places=4, default=0, verbose_name="Valor Total dos Produtos")
    valor_total_nota = models.DecimalField(max_digits=15, decimal_places=4, default=0, verbose_name="Valor Total da Nota")
    valor_total_icms = models.DecimalField(max_digits=15, decimal_places=4, default=0, verbose_name="Valor Total ICMS")
    valor_total_pis = models.DecimalField(max_digits=15, decimal_places=4, default=0, verbose_name="Valor Total PIS")
    valor_total_cofins = models.DecimalField(max_digits=15, decimal_places=4, default=0, verbose_name="Valor Total COFINS")
    valor_total_desconto = models.DecimalField(max_digits=15, decimal_places=4, default=0, verbose_name="Valor Total Desconto")
    
    condicao_pagamento = models.CharField(max_length=120, blank=True, null=True, verbose_name="Condicao de Pagamento")
    quantidade_parcelas = models.PositiveIntegerField(default=1, verbose_name="Quantidade de Parcelas")
    informacoes_adicionais = models.TextField(blank=True, null=True, verbose_name="InformaÃ§Ãµes Adicionais")

    class Meta:
        verbose_name = "Nota Fiscal"
        verbose_name_plural = "Notas Fiscais"
        ordering = ['-data_emissao', '-numero'] # OrdenaÃ§Ã£o padrÃ£o

    def __str__(self):
        nome_emitente = self.emitente_proprio or (self.emitente.razao_social if self.emitente else 'Emitente Desconhecido')
        return f"Nota {self.numero} Ã¢â‚¬â€œ {nome_emitente} ({self.chave_acesso})"

    # Se vocÃª removeu o campo 'fornecedor', ajuste seu cÃ³digo aqui ou em qualquer outro lugar que o use.
    # Se vocÃª pretende manter 'fornecedor' para outro propÃ³sito, o views.py atual nÃ£o o popula.


class TransporteNotaFiscal(models.Model):
    """Model para armazenar dados do transporte da Nota Fiscal."""
    nota_fiscal = models.OneToOneField(
        NotaFiscal,
        on_delete=models.CASCADE,
        related_name="transporte",
        verbose_name="Nota Fiscal"
    )
    transportadora = models.ForeignKey(
        Empresa,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='transportes',
        verbose_name='Cadastro da Transportadora'
    )
    modalidade_frete = models.CharField(
        max_length=2,
        choices=[
            ('0', 'ContrataÃ§Ã£o do Frete por conta do Remetente (CIF)'),
            ('1', 'ContrataÃ§Ã£o do Frete por conta do DestinatÃ¡rio (FOB)'),
            ('2', 'ContrataÃ§Ã£o do Frete por conta de Terceiros'),
            ('3', 'Transporte PrÃ³prio por conta do Remetente'),
            ('4', 'Transporte PrÃ³prio por conta do DestinatÃ¡rio'),
            ('9', 'Sem OcorrÃªncia de Transporte')
        ],
        blank=True, null=True,
        verbose_name="Modalidade do Frete"
    )
    transportadora_nome = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nome Transportadora")
    transportadora_cnpj = models.CharField(max_length=20, blank=True, null=True, verbose_name="CNPJ Transportadora")
    placa_veiculo = models.CharField(max_length=10, blank=True, null=True, verbose_name="Placa do VeÃ­culo")
    uf_veiculo = models.CharField(max_length=2, blank=True, null=True, verbose_name="UF do VeÃ­culo")
    rntc = models.CharField(max_length=20, blank=True, null=True, verbose_name="RNTC")
    quantidade_volumes = models.PositiveIntegerField(default=0, verbose_name="Quantidade de Volumes")
    especie_volumes = models.CharField(max_length=50, blank=True, null=True, verbose_name="EspÃ©cie dos Volumes")
    peso_liquido = models.DecimalField(max_digits=14, decimal_places=4, default=0, verbose_name="Peso LÃ­quido (kg)")
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
    numero = models.CharField(max_length=20, verbose_name="NÃºmero da Duplicata")
    valor = models.DecimalField(max_digits=15, decimal_places=4, verbose_name="Valor")
    vencimento = models.DateField(verbose_name="Data de Vencimento")

    class Meta:
        verbose_name = "Duplicata da Nota Fiscal"
        verbose_name_plural = "Duplicatas da Nota Fiscal"
        unique_together = ('nota_fiscal', 'numero') # Garante que nÃ£o hÃ¡ duplicatas com o mesmo nÃºmero para a mesma NF

    def __str__(self):
        return f"Duplicata {self.numero} da Nota {self.nota_fiscal.numero}"
    
class ItemNotaFiscal(models.Model):
    """Modelo para armazenar os itens de uma Nota Fiscal, incluindo seus detalhes fiscais.
    Estes campos refletem os valores e classificaÃ§Ãµes fiscais aplicados a cada item na NF.
    """
    nota_fiscal = models.ForeignKey(
        'NotaFiscal',
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name="Nota Fiscal"
    )
    produto = models.ForeignKey(
        'produto.Produto', # String para evitar dependÃªncia circular se 'produto' importa 'nota_fiscal'
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='itens_nota',
        verbose_name="Produto"
    )
    codigo = models.CharField(max_length=50, verbose_name="CÃ³digo do Produto")
    descricao = models.CharField(max_length=255, verbose_name="DescriÃ§Ã£o do Produto")
    ncm = models.CharField(max_length=10, blank=True, null=True, verbose_name="NCM")
    cfop = models.CharField(max_length=10, blank=True, null=True, verbose_name="CFOP")
    unidade = models.CharField(max_length=10, blank=True, null=True, verbose_name="Unidade Comercial")
    quantidade = models.DecimalField(max_digits=15, decimal_places=6, default=0, verbose_name="Quantidade")
    valor_unitario = models.DecimalField(max_digits=15, decimal_places=6, default=0, verbose_name="Valor UnitÃ¡rio")
    valor_total = models.DecimalField(max_digits=15, decimal_places=6, default=0, verbose_name="Valor Total")
    desconto = models.DecimalField(max_digits=15, decimal_places=6, blank=True, null=True, verbose_name="Valor Desconto")

    # Campos de impostos detalhados por item
    base_calculo_icms = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True, verbose_name="Base CÃ¡lculo ICMS")
    aliquota_icms = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="AlÃ­quota ICMS (%)")
    regra_icms_aplicada = models.ForeignKey('fiscal_regras.RegraAliquotaICMS', on_delete=models.SET_NULL, null=True, blank=True, related_name='itens_nota_aplicados', verbose_name='Regra ICMS Aplicada')
    regra_icms_descricao = models.CharField(max_length=255, blank=True, null=True, verbose_name='Descricao da Regra ICMS')
    aliquota_icms_origem = models.CharField(max_length=30, blank=True, null=True, verbose_name='Origem da Aliquota ICMS')
    motor_versao = models.CharField(max_length=40, blank=True, null=True, verbose_name='Versao do Motor Fiscal')
    dados_contexto_regra = models.JSONField(blank=True, null=True, verbose_name='Contexto da Regra Fiscal')
    valor_icms_desonerado = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True, verbose_name="Valor ICMS Desonerado")
    motivo_desoneracao_icms = models.CharField(max_length=2, blank=True, null=True, verbose_name="Motivo DesoneraÃ§Ã£o ICMS")
    cst_icms_cst_aplicado = models.ForeignKey(CST, on_delete=models.SET_NULL, null=True, blank=True, related_name='itens_icms_cst', verbose_name="CST ICMS Aplicado")
    cst_icms_csosn_aplicado = models.ForeignKey(CSOSN, on_delete=models.SET_NULL, null=True, blank=True, related_name='itens_icms_csosn', verbose_name="CSOSN ICMS Aplicado")

    base_calculo_ipi = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True, verbose_name="Base CÃ¡lculo IPI")
    aliquota_ipi = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="AlÃ­quota IPI (%)")
    cst_ipi_aplicado = models.ForeignKey(CST, on_delete=models.SET_NULL, null=True, blank=True, related_name='itens_ipi_cst', verbose_name="CST IPI Aplicado")

    base_calculo_pis = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True, verbose_name="Base CÃ¡lculo PIS")
    aliquota_pis = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="AlÃ­quota PIS (%)")
    cst_pis_aplicado = models.ForeignKey(CST, on_delete=models.SET_NULL, null=True, blank=True, related_name='itens_pis_cst', verbose_name="CST PIS Aplicado")

    base_calculo_cofins = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True, verbose_name="Base CÃ¡lculo COFINS")
    aliquota_cofins = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="AlÃ­quota COFINS (%)")
    cst_cofins_aplicado = models.ForeignKey(CST, on_delete=models.SET_NULL, null=True, blank=True, related_name='itens_cofins_cst', verbose_name="CST COFINS Aplicado")

    informacoes_adicionais_item = models.TextField(blank=True, null=True, verbose_name="InformaÃ§Ãµes Adicionais do Item")

    def save(self, *args, **kwargs):
        self.ncm = normalizar_codigo_ncm(self.ncm) or None
        super().save(*args, **kwargs)


