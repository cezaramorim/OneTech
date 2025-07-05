from django.db import models

class DetalhesFiscaisProduto(models.Model):
    """
    Modelo para armazenar detalhes fiscais específicos de um produto.
    Estes campos representam as configurações padrão de tributação para o produto,
    que podem ser usadas como base para cálculos em notas fiscais.
    """
    produto = models.OneToOneField(
        'produto.Produto',
        on_delete=models.CASCADE,
        related_name='detalhes_fiscais'
    )
    # ICMS
    cst_icms = models.CharField(max_length=5, blank=True, null=True, help_text="Código de Situação Tributária (CST/CSOSN) do ICMS")
    origem_mercadoria = models.CharField(max_length=1, blank=True, null=True, help_text="Origem da mercadoria (0-8)")
    aliquota_icms_interna = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Alíquota ICMS Interna (%)")
    aliquota_icms_interestadual = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Alíquota ICMS Interestadual (%)")
    reducao_base_icms = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Redução Base ICMS (%)")
    
    # IPI
    cst_ipi = models.CharField(max_length=2, blank=True, null=True, help_text="Código de Situação Tributária (CST) do IPI")
    aliquota_ipi = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Alíquota IPI (%)")

    # PIS
    cst_pis = models.CharField(max_length=2, blank=True, null=True, help_text="Código de Situação Tributária (CST) do PIS")
    aliquota_pis = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Alíquota PIS (%)")

    # COFINS
    cst_cofins = models.CharField(max_length=2, blank=True, null=True, help_text="Código de Situação Tributária (CST) do COFINS")
    aliquota_cofins = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Alíquota COFINS (%)")

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
