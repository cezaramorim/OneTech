import argparse
import re
from pathlib import Path

import pandas as pd

OUTPUT_HEADERS = [
    'uf_origem',
    'uf_destino',
    'aliquota_icms',
    'fcp',
    'reducao_base_icms',
    'modalidade',
    'tipo_operacao',
    'origem_mercadoria',
    'vigencia_inicio',
    'vigencia_fim',
    'prioridade',
    'ativo',
    'descricao',
]

UF_LIST = [
    'AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG',
    'PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO'
]

UF_RE = re.compile(r'^[A-Z]{2}$')


def normalize_uf(value):
    text = re.sub(r'[^A-Za-z]', '', str(value or '')).upper()
    text = text[:2]
    return text if UF_RE.match(text) else ''


def normalize_rate(value):
    text = str(value or '').strip().replace('%', '')
    if not text:
        return '0.00'

    if ',' in text and '.' in text:
        if text.rfind(',') > text.rfind('.'):
            text = text.replace('.', '').replace(',', '.')
        else:
            text = text.replace(',', '')
    else:
        text = text.replace(',', '.')

    try:
        return f'{float(text):.2f}'
    except Exception:
        return '0.00'


def load_any_table(path):
    suffix = path.suffix.lower()
    if suffix in {'.xlsx', '.xls'}:
        return pd.read_excel(path)
    if suffix in {'.csv', '.txt'}:
        try:
            return pd.read_csv(path, sep=';')
        except Exception:
            return pd.read_csv(path)
    raise ValueError(f'Formato nao suportado: {suffix}')


def build_from_long_format(df, vigencia_inicio, descricao_base, prioridade):
    cols = {c.lower().strip(): c for c in df.columns}

    origem_col = cols.get('uf_origem') or cols.get('origem') or cols.get('uf origem')
    destino_col = cols.get('uf_destino') or cols.get('destino') or cols.get('uf destino')
    aliquota_col = cols.get('aliquota_icms') or cols.get('aliquota') or cols.get('icms')

    if not (origem_col and destino_col and aliquota_col):
        return None

    rows = []
    for _, row in df.iterrows():
        uf_origem = normalize_uf(row.get(origem_col))
        uf_destino = normalize_uf(row.get(destino_col))
        if not uf_origem or not uf_destino:
            continue

        aliquota = normalize_rate(row.get(aliquota_col))
        modalidade = 'interna' if uf_origem == uf_destino else 'interestadual'

        rows.append({
            'uf_origem': uf_origem,
            'uf_destino': uf_destino,
            'aliquota_icms': aliquota,
            'fcp': normalize_rate(row.get(cols.get('fcp'))) if cols.get('fcp') else '0.00',
            'reducao_base_icms': normalize_rate(row.get(cols.get('reducao_base_icms'))) if cols.get('reducao_base_icms') else '0.00',
            'modalidade': modalidade,
            'tipo_operacao': str(row.get(cols.get('tipo_operacao')) or '1').strip()[:1] or '1',
            'origem_mercadoria': str(row.get(cols.get('origem_mercadoria')) or '').strip()[:1] or '',
            'vigencia_inicio': str(row.get(cols.get('vigencia_inicio')) or vigencia_inicio),
            'vigencia_fim': str(row.get(cols.get('vigencia_fim')) or '').strip(),
            'prioridade': int(row.get(cols.get('prioridade')) or prioridade),
            'ativo': str(row.get(cols.get('ativo')) or 'True'),
            'descricao': str(row.get(cols.get('descricao')) or f'{descricao_base} {uf_origem}->{uf_destino}').strip(),
        })
    return rows


def build_from_matrix_format(df, vigencia_inicio, descricao_base, prioridade):
    if df.empty or len(df.columns) < 2:
        return []

    first_col = df.columns[0]
    dest_cols = [c for c in df.columns[1:]]

    rows = []
    for _, row in df.iterrows():
        uf_origem = normalize_uf(row.get(first_col))
        if not uf_origem:
            continue

        for dc in dest_cols:
            uf_destino = normalize_uf(dc)
            if not uf_destino:
                continue

            aliquota_raw = row.get(dc)
            aliquota = normalize_rate(aliquota_raw)
            if aliquota == '0.00' and str(aliquota_raw).strip() in {'', 'nan', 'None'}:
                continue

            modalidade = 'interna' if uf_origem == uf_destino else 'interestadual'
            rows.append({
                'uf_origem': uf_origem,
                'uf_destino': uf_destino,
                'aliquota_icms': aliquota,
                'fcp': '0.00',
                'reducao_base_icms': '0.00',
                'modalidade': modalidade,
                'tipo_operacao': '1',
                'origem_mercadoria': '',
                'vigencia_inicio': vigencia_inicio,
                'vigencia_fim': '',
                'prioridade': prioridade,
                'ativo': 'True',
                'descricao': f'{descricao_base} {uf_origem}->{uf_destino}',
            })
    return rows


def build_blank_uf_matrix(vigencia_inicio, descricao_base, prioridade):
    rows = []
    for origem in UF_LIST:
        for destino in UF_LIST:
            modalidade = 'interna' if origem == destino else 'interestadual'
            rows.append({
                'uf_origem': origem,
                'uf_destino': destino,
                'aliquota_icms': '0.00',
                'fcp': '0.00',
                'reducao_base_icms': '0.00',
                'modalidade': modalidade,
                'tipo_operacao': '1',
                'origem_mercadoria': '',
                'vigencia_inicio': vigencia_inicio,
                'vigencia_fim': '',
                'prioridade': prioridade,
                'ativo': 'True',
                'descricao': f'{descricao_base} {origem}->{destino}',
            })
    return rows


def deduplicate(rows):
    seen = set()
    out = []
    for r in rows:
        key = (r['uf_origem'], r['uf_destino'], r['tipo_operacao'], r['modalidade'])
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def write_output(rows, output):
    out_df = pd.DataFrame(rows)
    for col in OUTPUT_HEADERS:
        if col not in out_df.columns:
            out_df[col] = ''
    out_df = out_df[OUTPUT_HEADERS]

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_excel(output_path, index=False)

    print(f'Arquivo gerado: {output_path}')
    print(f'Total linhas: {len(out_df)}')


def main():
    parser = argparse.ArgumentParser(description='Converte tabela ICMS origem/destino para layout da Central Fiscal.')
    parser.add_argument('--input', help='Arquivo de entrada (.xlsx, .xls, .csv, .txt).')
    parser.add_argument('--output', default='scripts/icms_origem_destino_para_central.xlsx', help='Arquivo de saida .xlsx.')
    parser.add_argument('--vigencia-inicio', default='', help='Data vigencia inicio (YYYY-MM-DD).')
    parser.add_argument('--prioridade', type=int, default=10, help='Prioridade padrao.')
    parser.add_argument('--descricao-base', default='Matriz ICMS', help='Descricao base para linhas geradas.')
    parser.add_argument('--generate-template-ufs', action='store_true', help='Gera matriz base com todas as UFs sem precisar de arquivo de entrada.')
    args = parser.parse_args()

    vigencia_inicio = args.vigencia_inicio.strip() or pd.Timestamp.today().date().isoformat()

    if args.generate_template_ufs:
        rows = build_blank_uf_matrix(vigencia_inicio, args.descricao_base, args.prioridade)
        write_output(rows, args.output)
        return

    if not args.input:
        raise SystemExit('Informe --input ou use --generate-template-ufs.')

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f'Arquivo nao encontrado: {input_path}')

    df = load_any_table(input_path)

    rows = build_from_long_format(df, vigencia_inicio, args.descricao_base, args.prioridade)
    if rows is None:
        rows = build_from_matrix_format(df, vigencia_inicio, args.descricao_base, args.prioridade)

    rows = deduplicate(rows)
    if not rows:
        raise SystemExit('Nenhuma linha valida foi encontrada na entrada.')

    write_output(rows, args.output)


if __name__ == '__main__':
    main()
