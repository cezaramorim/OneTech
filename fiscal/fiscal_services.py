import json
import math
import re
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from django.db import transaction
from django.utils import timezone

from .models import Cfop, NaturezaOperacao

DATA_DIR = Path(__file__).resolve().parent / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

FISCAL_SPECS = {
    'cfop': {
        'file_name': 'cfop.json',
        'model': Cfop,
        'required_columns': ['codigo', 'descricao'],
    },
    'natureza_operacao': {
        'file_name': 'natureza_operacao.json',
        'model': NaturezaOperacao,
        'required_columns': ['descricao'],
    },
    'icms_origem_destino': {
        'file_name': 'icms_origem_destino.json',
        'model': None,
        'required_columns': ['uf_origem', 'uf_destino', 'aliquota_icms'],
    },
}


def _get_spec(data_type):
    try:
        return FISCAL_SPECS[data_type]
    except KeyError as exc:
        raise ValueError(f'Tipo fiscal invalido: {data_type}') from exc


def _get_json_path(data_type):
    spec = _get_spec(data_type)
    return DATA_DIR / spec['file_name']


def _collapse_spaces(value):
    return re.sub(r'\s+', ' ', (value or '').strip())


def normalize_cfop_code(value):
    digits = re.sub(r'\D', '', str(value or ''))
    return digits[:4]


def normalize_natureza_code(value):
    cleaned = _collapse_spaces(str(value or ''))
    return cleaned.upper() or ''


def normalize_uf(value):
    cleaned = re.sub(r'[^A-Za-z]', '', str(value or '')).upper()
    return cleaned[:2]


def normalize_decimal(value, default='0'):
    if _is_empty(value):
        return default
    text = str(value).strip()
    text = text.replace('.', '').replace(',', '.') if (',' in text and '.' in text and text.rfind(',') > text.rfind('.')) else text.replace(',', '.')
    try:
        numeric_value = float(text)
        if not math.isfinite(numeric_value):
            return default
        return f"{numeric_value:.2f}"
    except Exception:
        return default


def _is_empty(value):
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except Exception:
        pass
    text = str(value).strip().lower()
    return text in {'', 'nan', 'nat', 'none', 'null'}


def _to_bool(value, default=True):
    if _is_empty(value):
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {'1', 'true', 't', 'sim', 's', 'y', 'yes'}:
        return True
    if text in {'0', 'false', 'f', 'nao', 'n', 'no'}:
        return False
    return default


def _to_int(value, default=10):
    if _is_empty(value):
        return default
    try:
        return int(float(str(value).strip().replace(',', '.')))
    except Exception:
        return default


def _to_date(value, default=None):
    if _is_empty(value):
        return default

    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if hasattr(value, 'to_pydatetime'):
        try:
            return value.to_pydatetime().date()
        except Exception:
            pass

    text = str(value).strip()
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(text, fmt).date()
        except Exception:
            continue

    parsed = pd.to_datetime(text, errors='coerce', dayfirst=True)
    if pd.isna(parsed):
        return default
    return parsed.date()

def normalize_cfop_record(record):
    return {
        'codigo': normalize_cfop_code(record.get('codigo')),
        'descricao': _collapse_spaces(str(record.get('descricao', ''))),
        'categoria': _collapse_spaces(str(record.get('categoria', ''))),
    }


def normalize_natureza_record(record):
    return {
        'codigo': normalize_natureza_code(record.get('codigo')),
        'descricao': _collapse_spaces(str(record.get('descricao', ''))),
        'observacoes': _collapse_spaces(str(record.get('observacoes', ''))),
    }


def normalize_icms_origem_destino_record(record):
    uf_origem = normalize_uf(record.get('uf_origem'))
    uf_destino = normalize_uf(record.get('uf_destino'))
    modalidade = (record.get('modalidade') or '').strip().lower()
    if modalidade not in {'interna', 'interestadual'}:
        modalidade = 'interna' if uf_origem and uf_destino and uf_origem == uf_destino else 'interestadual'
    vigencia_inicio = _to_date(record.get('vigencia_inicio'), default=timezone.localdate())
    vigencia_fim = _to_date(record.get('vigencia_fim'), default=None)

    return {
        'uf_origem': uf_origem,
        'uf_destino': uf_destino,
        'aliquota_icms': normalize_decimal(record.get('aliquota_icms'), default='0'),
        'fcp': normalize_decimal(record.get('fcp'), default='0'),
        'reducao_base_icms': normalize_decimal(record.get('reducao_base_icms'), default='0'),
        'modalidade': modalidade,
        'tipo_operacao': str(record.get('tipo_operacao') or '1').strip()[:1] or '1',
        'origem_mercadoria': (str(record.get('origem_mercadoria') or '').strip()[:1] or ''),
        'vigencia_inicio': vigencia_inicio.isoformat(),
        'vigencia_fim': vigencia_fim.isoformat() if vigencia_fim else None,
        'prioridade': _to_int(record.get('prioridade'), default=10),
        'ativo': _to_bool(record.get('ativo', True), default=True),
        'descricao': _collapse_spaces(str(record.get('descricao') or f"Matriz ICMS {uf_origem}->{uf_destino}")),
    }


def normalize_record(data_type, record):
    if data_type == 'cfop':
        return normalize_cfop_record(record)
    if data_type == 'natureza_operacao':
        return normalize_natureza_record(record)
    if data_type == 'icms_origem_destino':
        return normalize_icms_origem_destino_record(record)
    raise ValueError(f'Tipo fiscal invalido: {data_type}')


def parse_excel_to_records(file_obj, data_type):
    spec = _get_spec(data_type)
    df = pd.read_excel(file_obj, engine='openpyxl')

    missing = [col for col in spec['required_columns'] if col not in df.columns]
    if missing:
        missing_str = ', '.join(missing)
        raise ValueError(f'As seguintes colunas obrigatorias nao foram encontradas: {missing_str}.')

    records = []
    for _, row in df.iterrows():
        normalized = normalize_record(data_type, row.to_dict())
        if data_type == 'cfop':
            if not normalized['codigo'] or not normalized['descricao']:
                continue
        elif data_type == 'natureza_operacao':
            if not normalized['descricao']:
                continue
        else:
            if not normalized['uf_origem'] or not normalized['uf_destino']:
                continue
        records.append(normalized)
    return records


def save_local_data(data_type, records, source='excel_upload'):
    path = _get_json_path(data_type)
    payload = {
        'metadata': {
            'source': source,
            'updated_at': timezone.localtime().isoformat(),
            'item_count': len(records),
        },
        'items': records,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return payload


def load_local_data(data_type):
    path = _get_json_path(data_type)
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding='utf-8'))


def summarize_local_data(data_type):
    try:
        payload = load_local_data(data_type)
    except FileNotFoundError:
        return {
            'type': data_type,
            'exists': False,
            'item_count': 0,
            'updated_at': '',
            'source': '',
        }

    meta = payload.get('metadata') or {}
    items = payload.get('items') or []
    return {
        'type': data_type,
        'exists': True,
        'item_count': meta.get('item_count', len(items)),
        'updated_at': meta.get('updated_at', ''),
        'source': meta.get('source', ''),
    }


def update_local_data_from_excel(file_obj, data_type):
    records = parse_excel_to_records(file_obj, data_type)
    return save_local_data(data_type, records)


def _import_icms_origem_destino_to_regras(payload):
    from produto.models import NCM
    from fiscal_regras.models import RegraAliquotaICMS

    items = payload.get('items') or []
    ncm_codigos = list(
        NCM.objects.filter(detalhesfiscaisproduto__isnull=False)
        .values_list('codigo', flat=True)
        .distinct()
    )

    imported = 0
    with transaction.atomic():
        for ncm in ncm_codigos:
            ncm_prefixo = re.sub(r'\D', '', str(ncm or ''))
            if not ncm_prefixo:
                continue

            for item in items:
                uf_origem = normalize_uf(item.get('uf_origem'))
                uf_destino = normalize_uf(item.get('uf_destino'))
                if not uf_origem or not uf_destino:
                    continue

                modalidade = item.get('modalidade') or ('interna' if uf_origem == uf_destino else 'interestadual')
                tipo_operacao = (item.get('tipo_operacao') or '1')[:1]
                origem_mercadoria = (item.get('origem_mercadoria') or '').strip()[:1] or None
                vigencia_inicio = _to_date(item.get('vigencia_inicio'), default=timezone.localdate())
                vigencia_fim = _to_date(item.get('vigencia_fim'), default=None)

                regra_desc = (item.get('descricao') or '').strip() or f"ICMS {uf_origem}->{uf_destino}"
                defaults = {
                    'ativo': _to_bool(item.get('ativo', True), default=True),
                    'descricao': f"{regra_desc} | NCM {ncm_prefixo}",
                    'tipo_operacao': tipo_operacao,
                    'modalidade': modalidade,
                    'origem_mercadoria': origem_mercadoria,
                    'aliquota_icms': normalize_decimal(item.get('aliquota_icms'), default='0'),
                    'fcp': normalize_decimal(item.get('fcp'), default='0'),
                    'reducao_base_icms': normalize_decimal(item.get('reducao_base_icms'), default='0'),
                    'prioridade': _to_int(item.get('prioridade'), default=10),
                    'vigencia_inicio': vigencia_inicio,
                    'vigencia_fim': vigencia_fim,
                    'observacoes': 'Gerado via Central Fiscal (cruzamento NCM x Matriz UF).',
                }

                RegraAliquotaICMS.objects.update_or_create(
                    ncm_prefixo=ncm_prefixo,
                    tipo_operacao=tipo_operacao,
                    modalidade=modalidade,
                    uf_origem=uf_origem,
                    uf_destino=uf_destino,
                    defaults=defaults,
                )
                imported += 1

    return {'count': imported, 'ncm_count': len(ncm_codigos), 'linhas_matriz': len(items)}


def import_local_data_to_db(data_type):
    payload = load_local_data(data_type)
    items = payload.get('items') or []
    imported = 0

    if data_type == 'icms_origem_destino':
        result = _import_icms_origem_destino_to_regras(payload)
        result['metadata'] = payload.get('metadata') or {}
        return result

    with transaction.atomic():
        if data_type == 'cfop':
            for item in items:
                record = normalize_cfop_record(item)
                if not record['codigo'] or not record['descricao']:
                    continue
                Cfop.objects.update_or_create(
                    codigo=record['codigo'],
                    defaults={
                        'descricao': record['descricao'],
                        'categoria': record['categoria'],
                    },
                )
                imported += 1
        else:
            for item in items:
                record = normalize_natureza_record(item)
                if not record['descricao']:
                    continue
                lookup = {'descricao': record['descricao']}
                if record['codigo']:
                    lookup = {'codigo': record['codigo']}
                NaturezaOperacao.objects.update_or_create(
                    **lookup,
                    defaults={
                        'codigo': record['codigo'] or None,
                        'descricao': record['descricao'],
                        'observacoes': record['observacoes'],
                    },
                )
                imported += 1

    return {'count': imported, 'metadata': payload.get('metadata') or {}}


def _natureza_group_key(obj):
    codigo = normalize_natureza_code(obj.codigo)
    if codigo:
        return f'codigo:{codigo}'
    return f'descricao:{_collapse_spaces(obj.descricao).lower()}'


def inspect_duplicates(data_type):
    if data_type == 'icms_origem_destino':
        return {'group_count': 0, 'groups': [], 'duplicate_count': 0}

    model = _get_spec(data_type)['model']
    groups = {}

    for obj in model.objects.all().order_by('id'):
        if data_type == 'cfop':
            key = normalize_cfop_code(obj.codigo)
        else:
            key = _natureza_group_key(obj)
        groups.setdefault(key, []).append(obj)

    duplicates = []
    for key, items in groups.items():
        if len(items) < 2:
            continue
        keeper = items[0]
        duplicates.append({
            'key': key,
            'keeper_id': keeper.pk,
            'keeper_label': str(keeper),
            'duplicate_ids': [item.pk for item in items[1:]],
            'count': len(items) - 1,
        })

    return {
        'group_count': len(duplicates),
        'groups': duplicates,
        'duplicate_count': sum(group['count'] for group in duplicates),
    }


def consolidate_duplicates(data_type):
    if data_type == 'icms_origem_destino':
        return {'group_count': 0, 'groups': [], 'duplicate_count': 0}

    summary = inspect_duplicates(data_type)
    model = _get_spec(data_type)['model']

    with transaction.atomic():
        for group in summary['groups']:
            model.objects.filter(pk__in=group['duplicate_ids']).delete()

    return summary





