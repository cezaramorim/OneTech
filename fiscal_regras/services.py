import re
from dataclasses import dataclass
from decimal import Decimal

from django.utils import timezone

from control.models import Emitente
from empresas.models import Empresa
from produto.models import Produto
from produto.ncm_utils import normalizar_codigo_ncm

from .constants import MOTOR_VERSAO_PADRAO
from .selectors import regras_icms_vigentes


@dataclass
class ResolucaoAliquota:
    found: bool
    origem: str
    aliquota_icms: Decimal
    reducao_base_icms: Decimal
    fcp: Decimal
    regra_id: int | None
    regra_descricao: str
    contexto: dict
    cst_icms_id: int | None = None
    csosn_icms_id: int | None = None
    aliquota_ipi: Decimal | None = None
    aliquota_pis: Decimal | None = None
    aliquota_cofins: Decimal | None = None


def _normalize_uf(value):
    return (value or '').strip().upper() or None


def _to_decimal(value, default='0'):
    if value is None:
        return Decimal(default)
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


def _build_prefixes(ncm):
    codigo = re.sub(r'\D', '', str(ncm or ''))
    prefixes = []
    for size in (8, 7, 6, 5, 4, 3, 2):
        if len(codigo) >= size:
            prefixes.append(codigo[:size])
    return prefixes


def _pick_best_rule(regras, *, prefixes, uf_origem, uf_destino, modalidade, tipo_operacao, origem_mercadoria):
    prefix_rank = {value: len(value) for value in prefixes}

    candidatos = []
    for regra in regras:
        if regra.ncm_prefixo not in prefix_rank:
            continue
        if regra.tipo_operacao and regra.tipo_operacao != tipo_operacao:
            continue
        if regra.modalidade and regra.modalidade != modalidade:
            continue
        if regra.uf_origem and regra.uf_origem != uf_origem:
            continue
        if regra.uf_destino and regra.uf_destino != uf_destino:
            continue
        if regra.origem_mercadoria and origem_mercadoria and regra.origem_mercadoria != origem_mercadoria:
            continue

        score = (
            prefix_rank[regra.ncm_prefixo],
            1 if regra.uf_origem else 0,
            1 if regra.uf_destino else 0,
            1 if regra.modalidade else 0,
            1 if regra.tipo_operacao else 0,
            1 if regra.origem_mercadoria else 0,
            int(regra.prioridade or 0),
            int(regra.pk),
        )
        candidatos.append((score, regra))

    if not candidatos:
        return None

    candidatos.sort(key=lambda item: item[0], reverse=True)
    return candidatos[0][1]


def resolver_regra_icms_item(
    *,
    data_emissao=None,
    emitente_id=None,
    destinatario_id=None,
    uf_emitente=None,
    uf_destino=None,
    ncm=None,
    tipo_operacao='1',
    origem_mercadoria=None,
    produto_id=None,
):
    data_ref = data_emissao or timezone.localdate()
    if hasattr(data_ref, 'date'):
        data_ref = data_ref.date()

    produto = None
    if produto_id:
        produto = Produto.objects.filter(pk=produto_id).select_related('detalhes_fiscais').first()

    ncm_normalizado = normalizar_codigo_ncm(ncm)
    if not ncm_normalizado and produto:
        detalhes = getattr(produto, 'detalhes_fiscais', None)
        if detalhes and detalhes.ncm:
            ncm_normalizado = normalizar_codigo_ncm(detalhes.ncm.codigo)

    emitente_uf = _normalize_uf(uf_emitente)
    destino_uf = _normalize_uf(uf_destino)

    if not emitente_uf and emitente_id:
        emitente = Emitente.objects.filter(pk=emitente_id).only('uf').first()
        emitente_uf = _normalize_uf(getattr(emitente, 'uf', None))

    if not destino_uf and destinatario_id:
        empresa = Empresa.objects.filter(pk=destinatario_id).only('uf').first()
        destino_uf = _normalize_uf(getattr(empresa, 'uf', None))

    modalidade = None
    if emitente_uf and destino_uf:
        modalidade = 'interna' if emitente_uf == destino_uf else 'interestadual'

    if not origem_mercadoria and produto:
        detalhes = getattr(produto, 'detalhes_fiscais', None)
        origem_mercadoria = getattr(detalhes, 'origem_mercadoria', None)

    prefixes = _build_prefixes(ncm_normalizado)

    if prefixes:
        regras = regras_icms_vigentes(data_ref).select_related('cst_icms', 'csosn_icms').filter(ncm_prefixo__in=prefixes)
        regra_escolhida = _pick_best_rule(
            regras,
            prefixes=prefixes,
            uf_origem=emitente_uf,
            uf_destino=destino_uf,
            modalidade=modalidade,
            tipo_operacao=tipo_operacao,
            origem_mercadoria=origem_mercadoria,
        )
        if regra_escolhida:
            return ResolucaoAliquota(
                found=True,
                origem='automatica',
                aliquota_icms=_to_decimal(regra_escolhida.aliquota_icms),
                reducao_base_icms=_to_decimal(regra_escolhida.reducao_base_icms),
                fcp=_to_decimal(regra_escolhida.fcp),
                regra_id=regra_escolhida.pk,
                regra_descricao=regra_escolhida.descricao,
                cst_icms_id=regra_escolhida.cst_icms_id,
                csosn_icms_id=regra_escolhida.csosn_icms_id,
                contexto={
                    'motor_versao': MOTOR_VERSAO_PADRAO,
                    'ncm': ncm_normalizado,
                    'prefixes': prefixes,
                    'modalidade': modalidade,
                    'uf_emitente': emitente_uf,
                    'uf_destino': destino_uf,
                    'data_referencia': data_ref.isoformat(),
                    'tipo_operacao': tipo_operacao,
                },
            )

    detalhes = getattr(produto, 'detalhes_fiscais', None) if produto else None

    aliquota_interna = _to_decimal(getattr(detalhes, 'aliquota_icms_interna', None), default='0')
    aliquota_inter = _to_decimal(getattr(detalhes, 'aliquota_icms_interestadual', None), default='0')
    aliquota_icms = aliquota_interna if modalidade != 'interestadual' else (aliquota_inter or aliquota_interna)

    return ResolucaoAliquota(
        found=False,
        origem='fallback_produto' if detalhes else 'manual',
        aliquota_icms=aliquota_icms,
        reducao_base_icms=_to_decimal(getattr(detalhes, 'reducao_base_icms', None), default='0') if detalhes else Decimal('0'),
        fcp=Decimal('0'),
        regra_id=None,
        regra_descricao='Sem regra ativa para o contexto. Aplicado fallback do cadastro de produto.' if detalhes else 'Sem regra ativa para o contexto.',
        cst_icms_id=getattr(detalhes, 'cst_icms_cst_id', None) if detalhes else None,
        csosn_icms_id=getattr(detalhes, 'cst_icms_csosn_id', None) if detalhes else None,
        aliquota_ipi=_to_decimal(getattr(detalhes, 'ipi', None), default='0') if detalhes else None,
        aliquota_pis=_to_decimal(getattr(detalhes, 'pis', None), default='0') if detalhes else None,
        aliquota_cofins=_to_decimal(getattr(detalhes, 'cofins', None), default='0') if detalhes else None,
        contexto={
            'motor_versao': MOTOR_VERSAO_PADRAO,
            'ncm': ncm_normalizado,
            'prefixes': prefixes,
            'modalidade': modalidade,
            'uf_emitente': emitente_uf,
            'uf_destino': destino_uf,
            'data_referencia': data_ref.isoformat(),
            'tipo_operacao': tipo_operacao,
        },
    )
