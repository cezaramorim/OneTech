import json
import re
from datetime import datetime
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
}


def _get_spec(data_type):
    try:
        return FISCAL_SPECS[data_type]
    except KeyError as exc:
        raise ValueError(f'Tipo fiscal inv?lido: {data_type}') from exc



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



def normalize_record(data_type, record):
    if data_type == 'cfop':
        return normalize_cfop_record(record)
    return normalize_natureza_record(record)



def parse_excel_to_records(file_obj, data_type):
    spec = _get_spec(data_type)
    df = pd.read_excel(file_obj, engine='openpyxl')

    missing = [col for col in spec['required_columns'] if col not in df.columns]
    if missing:
        missing_str = ', '.join(missing)
        raise ValueError(f'As seguintes colunas obrigat?rias n?o foram encontradas: {missing_str}.')

    records = []
    for _, row in df.iterrows():
        normalized = normalize_record(data_type, row.to_dict())
        if data_type == 'cfop':
            if not normalized['codigo'] or not normalized['descricao']:
                continue
        else:
            if not normalized['descricao']:
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



def import_local_data_to_db(data_type):
    payload = load_local_data(data_type)
    items = payload.get('items') or []
    imported = 0

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
    summary = inspect_duplicates(data_type)
    model = _get_spec(data_type)['model']

    with transaction.atomic():
        for group in summary['groups']:
            model.objects.filter(pk__in=group['duplicate_ids']).delete()

    return summary
