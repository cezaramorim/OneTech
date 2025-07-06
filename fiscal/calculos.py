# fiscal/calculos.py

from decimal import Decimal
from fiscal.models import Cfop, NaturezaOperacao
from produto.models import Produto
from empresas.models import EmpresaAvancada
from nota_fiscal.models import ItemNotaFiscal, NotaFiscal

def calcular_impostos_item(
    item_nota_fiscal: ItemNotaFiscal,
    produto: Produto,
    emitente: EmpresaAvancada,
    destinatario: EmpresaAvancada
) -> dict:
    """
    Calcula os impostos (ICMS, IPI, PIS, COFINS) para um item de nota fiscal.
    Esta é uma implementação simplificada e deve ser expandida com as regras tributárias reais.

    Args:
        item_nota_fiscal: O objeto ItemNotaFiscal a ser calculado.
        produto: O objeto Produto associado ao item.
        emitente: O objeto EmpresaAvancada do emitente da nota.
        destinatario: O objeto EmpresaAvancada do destinatário da nota.

    Returns:
        Um dicionário contendo os valores calculados dos impostos e os CSTs aplicados.
    """
    # Valores padrão
    base_calculo_icms = Decimal('0.00')
    aliquota_icms = Decimal('0.00')
    valor_icms = Decimal('0.00')
    valor_icms_desonerado = Decimal('0.00')
    motivo_desoneracao_icms = ''
    cst_icms_aplicado = '90' # Exemplo: Outras Saídas

    base_calculo_ipi = Decimal('0.00')
    aliquota_ipi = Decimal('0.00')
    valor_ipi = Decimal('0.00')
    cst_ipi_aplicado = '99' # Exemplo: Outras Saídas

    base_calculo_pis = Decimal('0.00')
    aliquota_pis = Decimal('0.00')
    valor_pis = Decimal('0.00')
    cst_pis_aplicado = '99' # Exemplo: Outras Operações

    base_calculo_cofins = Decimal('0.00')
    aliquota_cofins = Decimal('0.00')
    valor_cofins = Decimal('0.00')
    cst_cofins_aplicado = '99' # Exemplo: Outras Operações

    # Lógica de cálculo (EXEMPLO - SUBSTITUIR POR REGRAS REAIS)
    # A complexidade aqui dependerá de NCM, CFOP, CST, regimes tributários, UF, etc.
    # Use os campos de DetalhesFiscaisProduto como ponto de partida.

    # Exemplo simplificado para ICMS:
    if produto.detalhes_fiscais and emitente.contribuinte_icms:
        # Se o produto tiver detalhes fiscais e o emitente for contribuinte de ICMS
        aliquota_icms = produto.detalhes_fiscais.aliquota_icms_interna or Decimal('0.00')
        base_calculo_icms = item_nota_fiscal.valor_total
        valor_icms = base_calculo_icms * (aliquota_icms / Decimal('100'))
        cst_icms_aplicado = produto.detalhes_fiscais.cst_icms or '00' # Tributado Integralmente

    # Exemplo simplificado para IPI:
    if produto.detalhes_fiscais:
        aliquota_ipi = produto.detalhes_fiscais.aliquota_ipi or Decimal('0.00')
        base_calculo_ipi = item_nota_fiscal.valor_total
        valor_ipi = base_calculo_ipi * (aliquota_ipi / Decimal('100'))
        cst_ipi_aplicado = produto.detalhes_fiscais.cst_ipi or '50' # Saída Tributada

    # Exemplo simplificado para PIS/COFINS:
    if produto.detalhes_fiscais:
        aliquota_pis = produto.detalhes_fiscais.aliquota_pis or Decimal('0.00')
        base_calculo_pis = item_nota_fiscal.valor_total
        valor_pis = base_calculo_pis * (aliquota_pis / Decimal('100'))
        cst_pis_aplicado = produto.detalhes_fiscais.cst_pis or '01' # Operação Tributável

        aliquota_cofins = produto.detalhes_fiscais.aliquota_cofins or Decimal('0.00')
        base_calculo_cofins = item_nota_fiscal.valor_total
        valor_cofins = base_calculo_cofins * (aliquota_cofins / Decimal('100'))
        cst_cofins_aplicado = produto.detalhes_fiscais.cst_cofins or '01' # Operação Tributável

    return {
        'base_calculo_icms': base_calculo_icms,
        'aliquota_icms': aliquota_icms,
        'valor_icms': valor_icms,
        'valor_icms_desonerado': valor_icms_desonerado,
        'motivo_desoneracao_icms': motivo_desoneracao_icms,
        'cst_icms_aplicado': cst_icms_aplicado,

        'base_calculo_ipi': base_calculo_ipi,
        'aliquota_ipi': aliquota_ipi,
        'valor_ipi': valor_ipi,
        'cst_ipi_aplicado': cst_ipi_aplicado,

        'base_calculo_pis': base_calculo_pis,
        'aliquota_pis': aliquota_pis,
        'valor_pis': valor_pis,
        'cst_pis_aplicado': cst_pis_aplicado,

        'base_calculo_cofins': base_calculo_cofins,
        'aliquota_cofins': aliquota_cofins,
        'valor_cofins': valor_cofins,
        'cst_cofins_aplicado': cst_cofins_aplicado,
    }

def aplicar_impostos_na_nota(nota_fiscal: NotaFiscal):
    """
    Aplica os cálculos de impostos a todos os itens de uma Nota Fiscal e atualiza os totais da nota.

    Args:
        nota_fiscal: O objeto NotaFiscal a ser processado.
    """
    total_icms_nf = Decimal('0.00')
    total_pis_nf = Decimal('0.00')
    total_cofins_nf = Decimal('0.00')

    for item in nota_fiscal.itens.all():
        # Garante que o produto e os detalhes fiscais estão carregados
        produto = item.produto
        if not produto:
            # Lidar com item sem produto associado, talvez logar um erro ou pular
            continue

        # Chama a função de cálculo para o item
        impostos_calculados = calcular_impostos_item(
            item,
            produto,
            nota_fiscal.emitente,
            nota_fiscal.destinatario
        )

        # Atualiza os campos do item com os valores calculados
        item.base_calculo_icms = impostos_calculados['base_calculo_icms']
        item.aliquota_icms = impostos_calculados['aliquota_icms']
        item.valor_icms = impostos_calculados['valor_icms']
        item.valor_icms_desonerado = impostos_calculados['valor_icms_desonerado']
        item.motivo_desoneracao_icms = impostos_calculados['motivo_desoneracao_icms']
        item.cst_icms_cst_aplicado = impostos_calculados['cst_icms_aplicado']
        item.cst_icms_csosn_aplicado = impostos_calculados['cst_icms_csosn_aplicado']

        item.base_calculo_ipi = impostos_calculados['base_calculo_ipi']
        item.aliquota_ipi = impostos_calculados['aliquota_ipi']
        item.valor_ipi = impostos_calculados['valor_ipi']
        item.cst_ipi_aplicado = impostos_calculados['cst_ipi_aplicado']

        item.base_calculo_pis = impostos_calculados['base_calculo_pis']
        item.aliquota_pis = impostos_calculados['aliquota_pis']
        item.valor_pis = impostos_calculados['valor_pis']
        item.cst_pis_aplicado = impostos_calculados['cst_pis_aplicado']

        item.base_calculo_cofins = impostos_calculados['base_calculo_cofins']
        item.aliquota_cofins = impostos_calculados['aliquota_cofins']
        item.valor_cofins = impostos_calculados['valor_cofins']
        item.cst_cofins_aplicado = impostos_calculados['cst_cofins_aplicado']
        item.save() # Salva o item com os impostos atualizados

        # Soma os totais para a nota fiscal
        total_icms_nf += item.valor_icms
        total_pis_nf += item.valor_pis
        total_cofins_nf += item.valor_cofins

    # Atualiza os totais de impostos na Nota Fiscal
    nota_fiscal.valor_total_icms = total_icms_nf
    nota_fiscal.valor_total_pis = total_pis_nf
    nota_fiscal.valor_total_cofins = total_cofins_nf
    nota_fiscal.save() # Salva a nota fiscal com os totais atualizados
