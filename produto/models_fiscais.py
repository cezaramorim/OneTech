from django.db import models
from fiscal.models import CST, CSOSN


class DetalhesFiscaisProduto(models.Model):
    """
    Modelo para armazenar detalhes fiscais específicos de um produto.
    Estes campos representam as configurações padrão de tributação para o produto,
    que podem ser usadas como base para cálculos em notas fiscais.
    """

    ORIGEM_MERCADORIA_CHOICES = [
        ('0', '0 - Nacional, exceto as indicadas nos códigos 3, 4, 5 e 8'),
        ('1', '1 - Estrangeira, importação direta'),
        ('2', '2 - Estrangeira, adquirida no mercado interno'),
        ('3', '3 - Nacional, conteúdo de importação superior a 40% e até 70%'),
        ('4', '4 - Nacional, produzida conforme processos produtivos básicos'),
        ('5', '5 - Nacional, conteúdo de importação até 40%'),
        ('6', '6 - Estrangeira, importação direta, sem similar nacional (CAMEX)'),
        ('7', '7 - Estrangeira, adquirida no mercado interno, sem similar nacional (CAMEX)'),
        ('8', '8 - Nacional, conteúdo de importação superior a 70%'),
    ]

    produto = models.OneToOneField(
        'produto.Produto',
        on_delete=models.CASCADE,
        related_name='detalhes_fiscais'
    )
    # ICMS
    cst_icms_cst = models.ForeignKey(CST, on_delete=models.SET_NULL, null=True, blank=True, related_name='produtos_icms_cst', verbose_name="CST ICMS")
    cst_icms_csosn = models.ForeignKey(CSOSN, on_delete=models.SET_NULL, null=True, blank=True, related_name='produtos_icms_csosn', verbose_name="CSOSN ICMS")
    origem_mercadoria = models.CharField(
        max_length=1,
        blank=True,
        null=True,
        choices=ORIGEM_MERCADORIA_CHOICES,
        help_text="Origem da mercadoria (0-8)",
    )
    aliquota_icms_interna = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Alíquota ICMS Interna (%)")
    aliquota_icms_interestadual = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Alíquota ICMS Interestadual (%)")
    reducao_base_icms = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Redução Base ICMS (%)")

    # IPI
    cst_ipi = models.ForeignKey(CST, on_delete=models.SET_NULL, null=True, blank=True, related_name='produtos_ipi_cst', verbose_name="CST IPI")

    # PIS
    cst_pis = models.ForeignKey(CST, on_delete=models.SET_NULL, null=True, blank=True, related_name='produtos_pis_cst', verbose_name="CST PIS")

    # COFINS
    cst_cofins = models.ForeignKey(CST, on_delete=models.SET_NULL, null=True, blank=True, related_name='produtos_cofins_cst', verbose_name="CST COFINS")

    # Outros
    cest = models.CharField(max_length=7, blank=True, null=True, help_text="Código Especificador da Substituição Tributária (CEST)")
    ncm = models.ForeignKey('produto.NCM', on_delete=models.SET_NULL, null=True, blank=True, help_text="Nomenclatura Comum do Mercosul")
    cfop = models.CharField(max_length=10, blank=True, null=True, help_text="Código Fiscal de Operações e Prestações")

    valor_unitario_comercial = models.DecimalField("Valor Unitário Comercial", max_digits=18, decimal_places=10, blank=True, null=True)
    icms = models.DecimalField(max_digits=18, decimal_places=10, blank=True, null=True)
    ipi = models.DecimalField(max_digits=18, decimal_places=10, blank=True, null=True)
    pis = models.DecimalField(max_digits=18, decimal_places=10, blank=True, null=True)
    cofins = models.DecimalField(max_digits=18, decimal_places=10, blank=True, null=True)
    unidade_comercial = models.CharField(max_length=10, blank=True, null=True, help_text="Unidade usada na nota (ex: UN, KG)")
    quantidade_comercial = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    codigo_produto_fornecedor = models.CharField(max_length=100, blank=True, null=True, help_text="Código interno do fornecedor (cProd)")
