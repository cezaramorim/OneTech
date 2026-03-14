import hashlib
import logging
import re
import time
from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.utils import timezone

from control.models import Emitente
from empresas.models import Empresa
from produto.models import Produto
from produto.ncm_utils import normalizar_codigo_ncm

from .constants import MOTOR_VERSAO_PADRAO
from .selectors import regras_icms_vigentes

logger = logging.getLogger(__name__)

METRICS_CACHE_KEY_PREFIX = 'fiscal_regras:metrics:'
METRICS_CACHE_TTL_SECONDS = 7 * 24 * 3600


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


def _to_string_or_none(value):
    if value is None:
        return None
    return str(value)


def _resolution_to_payload(resolucao):
    return {
        'found': bool(resolucao.found),
        'origem': resolucao.origem,
        'aliquota_icms': _to_string_or_none(resolucao.aliquota_icms),
        'reducao_base_icms': _to_string_or_none(resolucao.reducao_base_icms),
        'fcp': _to_string_or_none(resolucao.fcp),
        'regra_id': resolucao.regra_id,
        'regra_descricao': resolucao.regra_descricao,
        'contexto': resolucao.contexto or {},
        'cst_icms_id': resolucao.cst_icms_id,
        'csosn_icms_id': resolucao.csosn_icms_id,
        'aliquota_ipi': _to_string_or_none(resolucao.aliquota_ipi),
        'aliquota_pis': _to_string_or_none(resolucao.aliquota_pis),
        'aliquota_cofins': _to_string_or_none(resolucao.aliquota_cofins),
    }


def _payload_to_resolution(payload):
    return ResolucaoAliquota(
        found=bool(payload.get('found')),
        origem=payload.get('origem') or 'manual',
        aliquota_icms=_to_decimal(payload.get('aliquota_icms')),
        reducao_base_icms=_to_decimal(payload.get('reducao_base_icms')),
        fcp=_to_decimal(payload.get('fcp')),
        regra_id=payload.get('regra_id'),
        regra_descricao=payload.get('regra_descricao') or '',
        contexto=payload.get('contexto') or {},
        cst_icms_id=payload.get('cst_icms_id'),
        csosn_icms_id=payload.get('csosn_icms_id'),
        aliquota_ipi=_to_decimal(payload.get('aliquota_ipi')) if payload.get('aliquota_ipi') not in (None, '') else None,
        aliquota_pis=_to_decimal(payload.get('aliquota_pis')) if payload.get('aliquota_pis') not in (None, '') else None,
        aliquota_cofins=_to_decimal(payload.get('aliquota_cofins')) if payload.get('aliquota_cofins') not in (None, '') else None,
    )


def _get_metrics_cache_key(alias=None):
    db_alias = alias or connection.alias
    return f'{METRICS_CACHE_KEY_PREFIX}{db_alias}'


def _read_metrics(alias=None):
    key = _get_metrics_cache_key(alias)
    data = cache.get(key)
    if isinstance(data, dict):
        return data
    return {
        'total': 0,
        'found': 0,
        'fallback': 0,
        'errors': 0,
        'cache_hits': 0,
        'cache_misses': 0,
        'duration_total_ms': 0.0,
        'duration_avg_ms': 0.0,
        'last_error': '',
        'last_run_at': '',
    }


def _save_metrics(data, alias=None):
    key = _get_metrics_cache_key(alias)
    cache.set(key, data, timeout=METRICS_CACHE_TTL_SECONDS)


def _update_metrics(*, found=False, fallback=False, error=False, cache_hit=False, duration_ms=0.0, last_error=''):
    data = _read_metrics()
    data['total'] = int(data.get('total') or 0) + 1
    data['found'] = int(data.get('found') or 0) + (1 if found else 0)
    data['fallback'] = int(data.get('fallback') or 0) + (1 if fallback else 0)
    data['errors'] = int(data.get('errors') or 0) + (1 if error else 0)
    data['cache_hits'] = int(data.get('cache_hits') or 0) + (1 if cache_hit else 0)
    data['cache_misses'] = int(data.get('cache_misses') or 0) + (0 if cache_hit else 1)
    data['duration_total_ms'] = float(data.get('duration_total_ms') or 0.0) + float(duration_ms or 0.0)
    if data['total'] > 0:
        data['duration_avg_ms'] = round(data['duration_total_ms'] / data['total'], 4)
    data['last_run_at'] = timezone.now().isoformat()
    if last_error:
        data['last_error'] = str(last_error)
    _save_metrics(data)


def get_resolver_metrics_snapshot():
    return _read_metrics()


def _build_cache_key(*, data_ref, emitente_uf, destino_uf, modalidade, ncm_normalizado, tipo_operacao, origem_mercadoria, produto_id):
    raw = '|'.join(
        [
            connection.alias,
            str(data_ref or ''),
            str(emitente_uf or ''),
            str(destino_uf or ''),
            str(modalidade or ''),
            str(ncm_normalizado or ''),
            str(tipo_operacao or ''),
            str(origem_mercadoria or ''),
            str(produto_id or ''),
        ]
    )
    digest = hashlib.sha256(raw.encode('utf-8')).hexdigest()
    return f'fiscal_regras:resolver:{digest}'


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
    started_at = time.perf_counter()
    engine_enabled = bool(getattr(settings, 'FISCAL_REGRAS_ENGINE_ENABLED', True))
    cache_ttl = int(getattr(settings, 'FISCAL_REGRAS_CACHE_TTL', 60) or 0)

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

    cache_key = _build_cache_key(
        data_ref=data_ref,
        emitente_uf=emitente_uf,
        destino_uf=destino_uf,
        modalidade=modalidade,
        ncm_normalizado=ncm_normalizado,
        tipo_operacao=tipo_operacao,
        origem_mercadoria=origem_mercadoria,
        produto_id=produto_id,
    )

    if cache_ttl > 0:
        cached_payload = cache.get(cache_key)
        if isinstance(cached_payload, dict):
            resolucao_cached = _payload_to_resolution(cached_payload)
            duration_ms = round((time.perf_counter() - started_at) * 1000, 4)
            _update_metrics(
                found=resolucao_cached.found,
                fallback=not resolucao_cached.found,
                cache_hit=True,
                duration_ms=duration_ms,
            )
            return resolucao_cached

    try:
        if engine_enabled and prefixes:
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
                resolucao = ResolucaoAliquota(
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
                        'engine_enabled': engine_enabled,
                        'ncm': ncm_normalizado,
                        'prefixes': prefixes,
                        'modalidade': modalidade,
                        'uf_emitente': emitente_uf,
                        'uf_destino': destino_uf,
                        'data_referencia': data_ref.isoformat(),
                        'tipo_operacao': tipo_operacao,
                    },
                )
                if cache_ttl > 0:
                    cache.set(cache_key, _resolution_to_payload(resolucao), timeout=cache_ttl)
                duration_ms = round((time.perf_counter() - started_at) * 1000, 4)
                _update_metrics(found=True, fallback=False, cache_hit=False, duration_ms=duration_ms)
                return resolucao

        detalhes = getattr(produto, 'detalhes_fiscais', None) if produto else None

        aliquota_interna = _to_decimal(getattr(detalhes, 'aliquota_icms_interna', None), default='0')
        aliquota_inter = _to_decimal(getattr(detalhes, 'aliquota_icms_interestadual', None), default='0')
        aliquota_icms = aliquota_interna if modalidade != 'interestadual' else (aliquota_inter or aliquota_interna)

        resolucao_fallback = ResolucaoAliquota(
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
                'engine_enabled': engine_enabled,
                'ncm': ncm_normalizado,
                'prefixes': prefixes,
                'modalidade': modalidade,
                'uf_emitente': emitente_uf,
                'uf_destino': destino_uf,
                'data_referencia': data_ref.isoformat(),
                'tipo_operacao': tipo_operacao,
            },
        )
        if cache_ttl > 0:
            cache.set(cache_key, _resolution_to_payload(resolucao_fallback), timeout=cache_ttl)
        duration_ms = round((time.perf_counter() - started_at) * 1000, 4)
        _update_metrics(found=False, fallback=True, cache_hit=False, duration_ms=duration_ms)
        return resolucao_fallback
    except Exception as exc:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 4)
        _update_metrics(found=False, fallback=False, error=True, cache_hit=False, duration_ms=duration_ms, last_error=str(exc))
        logger.exception('Falha no motor fiscal_regras.')
        raise
