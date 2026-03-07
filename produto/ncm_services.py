import json
from pathlib import Path

from django.db import transaction

from produto.models import NCM
from produto.models_fiscais import DetalhesFiscaisProduto
from produto.ncm_utils import normalizar_codigo_ncm, normalizar_texto_mojibake


NCM_JSON_PATH = Path(__file__).resolve().parent / 'data' / 'ncm.json'


def get_ncm_json_path():
    return NCM_JSON_PATH


def load_ncm_json():
    with get_ncm_json_path().open(encoding='utf-8') as arquivo:
        return json.load(arquivo)


def save_ncm_json(data):
    caminho = get_ncm_json_path()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open('w', encoding='utf-8') as arquivo:
        json.dump(data, arquivo, ensure_ascii=False, indent=2)


def normalize_external_ncm_payload(payload, existing_metadata=None):
    existing_metadata = existing_metadata or {}
    if isinstance(payload, str):
        payload = json.loads(payload)

    if isinstance(payload, dict):
        nomenclaturas = payload.get('Nomenclaturas') or payload.get('nomenclaturas') or []
        data_atualizacao = payload.get('Data_Ultima_Atualizacao_NCM') or existing_metadata.get('Data_Ultima_Atualizacao_NCM', '')
        ato = payload.get('Ato') or existing_metadata.get('Ato', '')
    elif isinstance(payload, list):
        nomenclaturas = payload
        data_atualizacao = existing_metadata.get('Data_Ultima_Atualizacao_NCM', '')
        ato = existing_metadata.get('Ato', '')
    else:
        raise ValueError('Formato de payload NCM nao suportado.')

    normalized_items = []
    for item in nomenclaturas:
        if isinstance(item, dict):
            codigo = item.get('Codigo') or item.get('codigo')
            descricao = item.get('Descricao') or item.get('descricao')
            if codigo and descricao:
                normalized = dict(item)
                normalized['Codigo'] = codigo
                normalized['Descricao'] = normalizar_texto_mojibake(str(descricao).strip())
                normalized_items.append(normalized)
        elif isinstance(item, str) and '|' in item:
            codigo, descricao = item.split('|', 1)
            normalized_items.append({
                'Codigo': codigo.strip(),
                'Descricao': normalizar_texto_mojibake(descricao.strip()),
            })

    if not normalized_items:
        raise ValueError('Nenhuma nomenclatura valida encontrada na base oficial.')

    return {
        'Data_Ultima_Atualizacao_NCM': data_atualizacao,
        'Ato': ato,
        'Nomenclaturas': normalized_items,
    }


def import_ncm_from_local_json():
    data = load_ncm_json()
    nomenclaturas = data.get('Nomenclaturas', [])
    count = 0

    for item in nomenclaturas:
        codigo = item.get('Codigo')
        descricao = item.get('Descricao')
        if codigo and descricao:
            NCM.objects.update_or_create(
                codigo=normalizar_codigo_ncm(codigo),
                defaults={'descricao': normalizar_texto_mojibake(str(descricao).strip())},
            )
            count += 1

    return {
        'count': count,
        'metadata': {
            'vigencia': data.get('Data_Ultima_Atualizacao_NCM', ''),
            'ato': data.get('Ato', ''),
        },
    }


def inspect_ncm_duplicates():
    duplicates = {}
    for ncm in NCM.objects.all().order_by('id'):
        normalized = normalizar_codigo_ncm(ncm.codigo)
        duplicates.setdefault(normalized, []).append(ncm)

    groups = []
    for normalized, items in duplicates.items():
        if not normalized or len(items) <= 1:
            continue
        keeper = choose_keeper(items)
        others = [item for item in items if item.pk != keeper.pk]
        groups.append({
            'normalized_code': normalized,
            'keeper_id': keeper.pk,
            'keeper_codigo': keeper.codigo,
            'keeper_descricao': keeper.descricao,
            'duplicate_ids': [item.pk for item in others],
            'duplicate_count': len(others),
        })

    return {
        'group_count': len(groups),
        'duplicate_count': sum(group['duplicate_count'] for group in groups),
        'groups': groups,
    }


def consolidate_ncm_duplicates():
    summary = inspect_ncm_duplicates()

    for group in summary['groups']:
        keeper = NCM.objects.get(pk=group['keeper_id'])
        duplicates = list(NCM.objects.filter(pk__in=group['duplicate_ids']).order_by('id'))

        with transaction.atomic():
            for duplicate in duplicates:
                DetalhesFiscaisProduto.objects.filter(ncm_id=duplicate.pk).update(ncm=keeper)
                duplicate.delete()

            normalized_code = group['normalized_code']
            if keeper.codigo != normalized_code:
                keeper.codigo = normalized_code
                keeper.save(update_fields=['codigo'])

    return summary


def choose_keeper(items):
    def score(item):
        descricao = (item.descricao or '').strip()
        placeholder = descricao.lower() == f"ncm {normalizar_codigo_ncm(item.codigo)}".lower()
        return (placeholder, -len(descricao), item.pk)

    return sorted(items, key=score)[0]
