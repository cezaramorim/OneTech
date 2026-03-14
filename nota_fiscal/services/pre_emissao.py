from decimal import Decimal
from datetime import timedelta
import re


def _to_decimal(value, default='0'):
    if value is None:
        return Decimal(default)
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


def _extrair_dias_vencimento(condicao_pagamento, quantidade_parcelas):
    parcelas = max(int(quantidade_parcelas or 1), 1)
    texto = ' '.join(str(condicao_pagamento or '').strip().lower().split())
    numeros = [int(valor) for valor in re.findall(r'\d+', texto)]

    if not numeros and ('a vista' in texto or 'avista' in texto):
        numeros = [0]
    if not numeros:
        return [idx * 30 for idx in range(parcelas)]
    if len(numeros) >= parcelas:
        return [max(int(v), 0) for v in numeros[:parcelas]]
    if len(numeros) == 1:
        base = max(int(numeros[0]), 0)
        return [base * (idx + 1) for idx in range(parcelas)]

    dias = [max(int(v), 0) for v in numeros]
    ultimo = dias[-1]
    while len(dias) < parcelas:
        ultimo += 30
        dias.append(ultimo)
    return dias


def validar_nota_pre_emissao(nota):
    errors = []
    warnings = []

    if str(nota.tipo_operacao or '') != '1':
        errors.append({'field': 'tipo_operacao', 'message': 'Somente notas de saida podem ser emitidas.'})

    cabecalho_minimo = [
        ('emitente_proprio_id', 'Emitente'),
        ('destinatario_id', 'Destinatario'),
        ('natureza_operacao', 'Natureza da Operacao'),
        ('finalidade_emissao', 'Finalidade da Emissao'),
        ('tipo_operacao', 'Tipo de Operacao'),
        ('modelo_documento', 'Modelo do Documento'),
        ('ambiente', 'Ambiente'),
        ('data_emissao', 'Data de Emissao'),
        ('numero', 'Numero'),
    ]
    for attr, label in cabecalho_minimo:
        value = getattr(nota, attr, None)
        if value is None or str(value).strip() == '':
            errors.append({'field': attr, 'message': f'Campo obrigatorio para emissao: {label}.'})

    itens = list(nota.itens.all())
    if not itens:
        errors.append({'field': 'itens', 'message': 'A nota precisa ter ao menos um item para emissao.'})
    else:
        soma_itens = Decimal('0')
        for idx, item in enumerate(itens, start=1):
            if not (item.codigo or '').strip():
                errors.append({'field': f'item_{idx}.codigo', 'message': 'Codigo do item obrigatorio.'})
            if not (item.descricao or '').strip():
                errors.append({'field': f'item_{idx}.descricao', 'message': 'Descricao do item obrigatoria.'})
            if not (item.ncm or '').strip():
                errors.append({'field': f'item_{idx}.ncm', 'message': 'NCM do item obrigatorio.'})
            if not (item.cfop or '').strip():
                errors.append({'field': f'item_{idx}.cfop', 'message': 'CFOP do item obrigatorio.'})
            if _to_decimal(item.quantidade) <= 0:
                errors.append({'field': f'item_{idx}.quantidade', 'message': 'Quantidade do item deve ser maior que zero.'})
            if _to_decimal(item.valor_unitario) < 0:
                errors.append({'field': f'item_{idx}.valor_unitario', 'message': 'Valor unitario do item nao pode ser negativo.'})
            soma_itens += _to_decimal(item.valor_total)

            origem_aliquota = (item.aliquota_icms_origem or '').strip().lower()
            if not origem_aliquota:
                warnings.append({'field': f'item_{idx}.aliquota_icms_origem', 'message': 'Origem da aliquota ICMS nao informada.'})

        total_nota = _to_decimal(nota.valor_total_nota)
        if abs(soma_itens - total_nota) > Decimal('0.01'):
            errors.append(
                {
                    'field': 'valor_total_nota',
                    'message': 'Valor total da nota diverge da soma dos itens.',
                    'expected': str(soma_itens),
                    'current': str(total_nota),
                }
            )

    duplicatas = list(nota.duplicatas.all())
    if duplicatas:
        parcelas_esperadas = max(int(nota.quantidade_parcelas or 1), 1)
        if len(duplicatas) != parcelas_esperadas:
            errors.append(
                {
                    'field': 'duplicatas',
                    'message': 'Quantidade de duplicatas difere da quantidade de parcelas.',
                    'expected': str(parcelas_esperadas),
                    'current': str(len(duplicatas)),
                }
            )

        total_duplicatas = sum((_to_decimal(d.valor) for d in duplicatas), Decimal('0'))
        total_nota = _to_decimal(nota.valor_total_nota)
        if abs(total_duplicatas - total_nota) > Decimal('0.01'):
            errors.append(
                {
                    'field': 'duplicatas',
                    'message': 'Soma das duplicatas diverge do valor total da nota.',
                    'expected': str(total_nota),
                    'current': str(total_duplicatas),
                }
            )

        if nota.data_emissao:
            dias_esperados = _extrair_dias_vencimento(nota.condicao_pagamento, parcelas_esperadas)
            duplicatas_ordenadas = sorted(
                duplicatas,
                key=lambda d: int(''.join(ch for ch in str(d.numero or '') if ch.isdigit()) or 0)
            )
            for idx, duplicata in enumerate(duplicatas_ordenadas[:parcelas_esperadas]):
                esperado = nota.data_emissao + timedelta(days=dias_esperados[idx])
                if duplicata.vencimento and duplicata.vencimento != esperado:
                    errors.append(
                        {
                            'field': f'duplicata_{idx + 1}.vencimento',
                            'message': 'Vencimento da duplicata divergente da condicao de pagamento.',
                            'expected': str(esperado),
                            'current': str(duplicata.vencimento),
                        }
                    )

    snapshot = {
        'nota_id': nota.pk,
        'tipo_operacao': nota.tipo_operacao,
        'numero': nota.numero,
        'itens_count': len(itens),
        'duplicatas_count': len(duplicatas),
    }

    return {
        'ok': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'snapshot': snapshot,
    }
