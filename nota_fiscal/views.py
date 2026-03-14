# nota_fiscal/views.py

import os
import re
import json
import traceback
import datetime
import xml.etree.ElementTree as ET
from decimal import Decimal

from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from common.messages_utils import get_app_messages
from accounts.utils.decorators import login_required_json, permission_required_json
from django.core.files.storage import default_storage
from django.db import transaction, DatabaseError
from django.db.models import Q, IntegerField
from django.db.models.functions import Cast
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.text import slugify
# Removido o @csrf_exempt por razÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âµes de seguranÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§a
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from common.utils import render_ajax_or_base
from common.utils.formatters import converter_valor_br, converter_data_para_date, CustomDecimalEncoder
from fiscal.calculos import aplicar_impostos_na_nota
from empresas.models import Empresa, CategoriaEmpresa
from control.models import Emitente
from produto.models import CategoriaProduto, Produto, UnidadeMedida, DetalhesFiscaisProduto, NCM
from produto.ncm_utils import formatar_codigo_ncm, normalizar_codigo_ncm
from fiscal.models import CST, CSOSN, NaturezaOperacao
from fiscal_regras.services import resolver_regra_icms_item
from .models import NotaFiscal, TransporteNotaFiscal, DuplicataNotaFiscal, ItemNotaFiscal
from produto.models_entradas import EntradaProduto
from .forms import (
    NotaFiscalForm,
    NotaFiscalEntradaForm,
    ItemNotaFiscalFormSet,
    DuplicataNotaFiscalFormSet,
    TransporteNotaFiscalFormSet,
    NotaFiscalSaidaForm
)

# --- Seguranca de contexto/tenant --- #
def _get_emitente_ativo_id(request):
    tenant = getattr(request, 'tenant', None)
    emitente_ativo_id = getattr(tenant, 'emitente_padrao_id', None)
    if not emitente_ativo_id:
        emitente_ativo_id = Emitente.objects.filter(is_default=True).values_list('id', flat=True).first()
    return emitente_ativo_id


def _nota_saida_fora_emitente_ativo(request, nota):
    if str(nota.tipo_operacao or '') != '1':
        return False
    emitente_ativo_id = _get_emitente_ativo_id(request)
    if not emitente_ativo_id:
        return True
    return int(nota.emitente_proprio_id or 0) != int(emitente_ativo_id)


def _extrair_dias_vencimento(condicao_pagamento, quantidade_parcelas):
    parcelas = max(int(quantidade_parcelas or 1), 1)
    texto = ' '.join(str(condicao_pagamento or '').strip().lower().split())
    numeros = [int(valor) for valor in re.findall(r'\d+', texto)]

    if not numeros and ('a vista' in texto or 'avista' in texto):
        numeros = [0]

    if not numeros:
        return [idx * 30 for idx in range(parcelas)]

    if len(numeros) >= parcelas:
        dias = numeros[:parcelas]
    elif len(numeros) == 1:
        base = max(numeros[0], 0)
        dias = [base * (idx + 1) for idx in range(parcelas)]
    else:
        dias = list(numeros)
        ultimo = max(dias[-1], 0)
        while len(dias) < parcelas:
            ultimo += 30
            dias.append(ultimo)

    normalizados = []
    anterior = 0
    for dia in dias:
        atual = max(int(dia), 0)
        if atual < anterior:
            atual = anterior
        normalizados.append(atual)
        anterior = atual

    return normalizados


def _sincronizar_duplicatas_nota(nota):
    parcelas_desejadas = max(int(nota.quantidade_parcelas or 1), 1)
    duplicatas_atuais = list(nota.duplicatas.order_by('id'))

    if len(duplicatas_atuais) > parcelas_desejadas:
        ids_excedentes = [dup.id for dup in duplicatas_atuais[parcelas_desejadas:]]
        DuplicataNotaFiscal.objects.filter(id__in=ids_excedentes).delete()
        duplicatas_atuais = duplicatas_atuais[:parcelas_desejadas]

    if len(duplicatas_atuais) < parcelas_desejadas:
        faltantes = parcelas_desejadas - len(duplicatas_atuais)
        for idx in range(faltantes):
            numero_seq = len(duplicatas_atuais) + idx + 1
            DuplicataNotaFiscal.objects.create(
                nota_fiscal=nota,
                numero=str(numero_seq).zfill(3),
                vencimento=nota.data_emissao or timezone.localdate(),
                valor=Decimal('0.00'),
            )

    duplicatas = list(nota.duplicatas.order_by('id')[:parcelas_desejadas])
    dias = _extrair_dias_vencimento(nota.condicao_pagamento, parcelas_desejadas)

    total_nota = Decimal(str(nota.valor_total_nota or 0))
    total_desconto = Decimal(str(nota.valor_total_desconto or 0))
    valor_liquido = total_nota - total_desconto
    if valor_liquido < 0:
        valor_liquido = Decimal('0')

    total_centavos = int((valor_liquido * Decimal('100')).quantize(Decimal('1')))
    base_centavos = total_centavos // parcelas_desejadas
    resto_centavos = total_centavos - (base_centavos * parcelas_desejadas)
    base_date = nota.data_emissao or timezone.localdate()

    for idx, dup in enumerate(duplicatas):
        parcela_centavos = base_centavos + (1 if resto_centavos > 0 else 0)
        if resto_centavos > 0:
            resto_centavos -= 1
        dup.numero = str(idx + 1).zfill(3)
        dup.vencimento = base_date + datetime.timedelta(days=dias[idx])
        dup.valor = Decimal(parcela_centavos) / Decimal('100')
        dup.save(update_fields=['numero', 'vencimento', 'valor'])

# --- FunÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âµes Auxiliares de Parsing --- #

def strip_namespace(tag):
    """Remove o namespace (ex: {http://...}) de uma tag XML."""
    return tag.split('}')[-1]

def xml_to_dict(element):
    """Converte um elemento XML e seus filhos em um dicionÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡rio, tratando namespaces."""
    result = {strip_namespace(element.tag): {}}
    
    # Adiciona atributos do elemento
    if element.attrib:
        result[strip_namespace(element.tag)].update(element.attrib)

    # Adiciona filhos
    for child in element:
        child_dict = xml_to_dict(child)
        child_tag = strip_namespace(child.tag)

        # Se a tag jÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡ existe, transforma em lista para agrupar mÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âºltiplos elementos
        if child_tag in result[strip_namespace(element.tag)]:
            if not isinstance(result[strip_namespace(element.tag)][child_tag], list):
                result[strip_namespace(element.tag)][child_tag] = [result[strip_namespace(element.tag)][child_tag]]
            result[strip_namespace(element.tag)][child_tag].append(child_dict[child_tag])
        else:
            result[strip_namespace(element.tag)].update(child_dict)

    # Adiciona o texto do elemento, se houver
    if element.text and element.text.strip():
        text = element.text.strip()
        # Se jÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡ houver filhos, adiciona o texto como uma chave especial
        if len(result[strip_namespace(element.tag)]) > 0:
            result[strip_namespace(element.tag)]['#text'] = text
        # SenÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o, o valor da tag ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© apenas o texto
        else:
            result[strip_namespace(element.tag)] = text
            
    return result

# --- Views Principais --- #

@login_required_json
@permission_required_json('integracao_nfe.can_emit_nfe', raise_exception=True)
@require_GET
def emitir_nfe_list_view(request):
    """
    Lista as notas fiscais que estÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o prontas para serem emitidas (status em branco ou 'rascunho').
    """
    # Filtra notas do emitente que ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© o tenant atual e que ainda nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o foram enviadas.
    # O status pode ser '' (vazio) ou um status especÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â­fico como 'rascunho'.
    tenant = getattr(request, 'tenant', None)
    emitente_ativo_id = getattr(tenant, 'emitente_padrao_id', None)
    if not emitente_ativo_id:
        emitente_ativo_id = Emitente.objects.filter(is_default=True).values_list('id', flat=True).first()

    termo_busca = (request.GET.get('busca') or '').strip()

    notas_para_emitir = NotaFiscal.objects.filter(
        tipo_operacao='1'
    ).filter(
        Q(status_sefaz__isnull=True) | Q(status_sefaz='') | Q(status_sefaz='rascunho')
    )

    if emitente_ativo_id:
        notas_para_emitir = notas_para_emitir.filter(emitente_proprio_id=emitente_ativo_id)
    else:
        notas_para_emitir = notas_para_emitir.filter(emitente_proprio__isnull=False)

    if termo_busca:
        notas_para_emitir = notas_para_emitir.filter(
            Q(numero__icontains=termo_busca)
            | Q(destinatario__razao_social__icontains=termo_busca)
            | Q(destinatario__nome_fantasia__icontains=termo_busca)
            | Q(destinatario__nome__icontains=termo_busca)
            | Q(chave_acesso__icontains=termo_busca)
        )

    notas_para_emitir = notas_para_emitir.select_related('destinatario').order_by('-data_emissao')

    context = {
        'notas_para_emitir': notas_para_emitir,
        'termo_busca': termo_busca,
        'content_template': 'partials/nota_fiscal/emitir_nfe_list.html',
        'data_page': 'emitir_nfe_list',
    }
    
    return render_ajax_or_base(request, context['content_template'], context)


@login_required_json
@permission_required_json('nota_fiscal.add_notafiscal', raise_exception=True)
@require_GET
def importar_xml_view(request):
    """Renderiza a pÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡gina de upload de XML para importaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o de notas fiscais."""
    categorias = list(CategoriaProduto.objects.order_by("nome").values("id", "nome"))
    context = {
        'categorias': categorias,
        'data_page': 'importar_xml',
        'data_tela': 'importar_xml',
    }
    return render_ajax_or_base(request, 'partials/nota_fiscal/importar_xml.html', context)


@login_required_json
@require_POST
def importar_xml_nfe_view(request):
    """
    Recebe um arquivo XML, faz o parsing e retorna um JSON estruturado para preview.
    """
    app_messages = get_app_messages(request)
    xml_file = request.FILES.get('xml')
    if not request.user.has_perm('nota_fiscal.can_import_xml'):
        message = app_messages.error('Voce nao tem permissao para importar XML de Notas Fiscais.')
        return JsonResponse({'success': False, 'message': message, 'code': 'permission_denied'}, status=403)
    if not xml_file or not xml_file.name.lower().strip().endswith('.xml'):
        message = app_messages.error('Arquivo XML invalido ou nao fornecido.')
        return JsonResponse({'success': False, 'message': message}, status=400)
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        full_xml_dict = xml_to_dict(root).get('nfeProc', {})
        infNFe = full_xml_dict.get('NFe', {}).get('infNFe', {})
        if not infNFe:
            message = app_messages.error('Estrutura do XML invalida: <infNFe> nao encontrado.')
            return JsonResponse({'success': False, 'message': message}, status=400)
        chave = infNFe.get('Id', '').replace('NFe', '')
        if not chave:
            message = app_messages.error('Nao foi possivel extrair a chave de acesso do XML.')
            return JsonResponse({'success': False, 'message': message}, status=400)
        is_duplicate = NotaFiscal.objects.filter(chave_acesso=chave).exists()
        ide = infNFe.get('ide', {})
        emit = infNFe.get('emit', {})
        total = infNFe.get('total', {}).get('ICMSTot', {})
        nome_razao_social_emitente = emit.get('xNome', 'Nome do Emitente nao encontrado')
        itens_para_revisar = []
        det_list = infNFe.get('det', [])
        if not isinstance(det_list, list):
            det_list = [det_list]
        for det_item in det_list:
            prod = det_item.get('prod', {})
            codigo_importado = prod.get('cProd', '')
            produto_existente = Produto.objects.filter(codigo_fornecedor=codigo_importado).first()
            if not produto_existente:
                itens_para_revisar.append({
                    'nItem': det_item.get('@nItem', ''),
                    'codigo_produto': codigo_importado,
                    'descricao_produto': prod.get('xProd', ''),
                    'ncm': formatar_codigo_ncm(prod.get('NCM', '')),
                })
        message = 'XML processado com sucesso. Verifique os itens para revisao de categoria, se houver.'
        if is_duplicate:
            message = (
                f'Esta Nota Fiscal (Chave: {chave}) ja existe no sistema. '
                'Deseja importa-la novamente e atualizar os dados existentes?'
            )
        response_payload_for_frontend = {
            'success': True,
            'message': message,
            'is_duplicate': is_duplicate,
            'raw_payload': full_xml_dict,
            'chave_acesso': chave,
            'numero': ide.get('nNF', ''),
            'valor_total_nota': total.get('vNF', '0'),
            'data_emissao': ide.get('dhEmi') or ide.get('dEmi', ''),
            'itens_para_revisar': itens_para_revisar,
            'nome_razao_social': nome_razao_social_emitente,
        }
        return JsonResponse(response_payload_for_frontend, encoder=CustomDecimalEncoder)
    except Exception as e:
        message = app_messages.error(f'Ocorreu um erro no servidor ao processar o XML: {str(e)}')
        return JsonResponse({'success': False, 'message': message}, status=500)

@login_required_json
@permission_required_json('nota_fiscal.can_import_xml', raise_exception=True)
# @csrf_exempt REMOVIDO: `require_POST` jÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡ garante a proteÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o CSRF adequada para POST requests.
@require_POST
@transaction.atomic # Garante que todas as operaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âµes de banco de dados sejam atÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â´micas
def processar_importacao_xml_view(request):
    app_messages = get_app_messages(request)
    """
    View unificada que recebe o JSON da nota (com categorias dos produtos jÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡ definidas),
    valida e salva a nota fiscal e todos os seus dados relacionados (empresas, produtos, itens, etc.)
    em uma ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âºnica transaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o.
    """
    print("--- Iniciando processamento e salvamento da importaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o ---")
    try:
        payload = json.loads(request.body.decode('utf-8'))
        chave = payload.get('chave_acesso')
        force_update = payload.get('force_update', False)
        raw_payload = payload.get('raw_payload', {})

        if not chave or not raw_payload:
            return JsonResponse({'success': False, 'message': app_messages.error('Dados essenciais (chave de acesso ou payload) nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o encontrados.')}, status=400)

        infNFe = raw_payload.get('NFe', {}).get('infNFe', {})
        if not infNFe:
            return JsonResponse({'success': False, 'message': app_messages.error('Estrutura do XML invÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡lida: <infNFe> nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o encontrado no raw_payload.')}, status=400)

        # Verifica se a nota fiscal jÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡ existe
        nota_existente = NotaFiscal.objects.filter(chave_acesso=chave).first()
        if nota_existente:
            if not force_update:
                message = app_messages.warning(f'A Nota Fiscal "{nota_existente.numero}" jÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡ foi importada. Deseja substituir os dados existentes?')
                return JsonResponse({
                    'success': True, 'message': message, 'nota_existente': True,
                    'nota_id': nota_existente.pk, 'redirect_url': reverse('nota_fiscal:entradas_nota')
                }, status=200)
            else:
                print(f"--- Excluindo nota fiscal existente (ID: {nota_existente.pk}) para atualizaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o ---")
                nota_existente.delete()

        # 1. Processar Empresas (Emitente e DestinatÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡rio)
        emitente = _get_or_create_empresa(infNFe.get('emit', {}), 'emit')
        destinatario = _get_or_create_empresa(infNFe.get('dest', {}), 'dest')

        # 2. Criar a Nota Fiscal principal
        ide = infNFe.get('ide', {})
        total = infNFe.get('total', {}).get('ICMSTot', {})
        nf = NotaFiscal.objects.create(
            raw_payload=raw_payload,
            chave_acesso=chave,
            created_by=request.user,
            data_emissao=_parse_datetime(ide.get('dhEmi') or ide.get('dEmi')),
            data_saida=_parse_datetime(ide.get('dhSaiEnt') or ide.get('dSaiEnt')),
            numero=ide.get('nNF', ''),
            natureza_operacao=ide.get('natOp', ''),
            tipo_operacao='0',
            finalidade_emissao=(ide.get('finNFe') or None),
            modelo_documento=(ide.get('mod') or '55'),
            ambiente=(ide.get('tpAmb') or ('2' if settings.DEBUG else '1')),
            informacoes_adicionais=infNFe.get('infAdic', {}).get('infCpl', ''),
            valor_total_nota=Decimal(total.get('vNF', '0')),
            valor_total_produtos=Decimal(total.get('vProd', '0')),
            valor_total_icms=Decimal(total.get('vICMS', '0')),
            valor_total_pis=Decimal(total.get('vPIS', '0')),
            valor_total_cofins=Decimal(total.get('vCOFINS', '0')),
            valor_total_desconto=Decimal(total.get('vDesc', '0')),
            emitente=emitente,
            destinatario=destinatario,
        )
        print(f"DEBUG: Nota Fiscal {nf.numero} (ID: {nf.pk}) criada.")

        # Mapeamento de cÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â³digo de produto para categoria para acesso rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡pido
        categorias_mapeadas = {str(p.get('codigo_produto')): p.get('categoria_id') for p in payload.get('itens_para_revisar', [])}

        # 3. PRE-PROCESSAMENTO AGREGADO PARA ATUALIZACAO DE PRODUTOS
        produtos_agregados = {}
        det_list = infNFe.get('det', [])
        if not isinstance(det_list, list):
            det_list = [det_list]

        for item_data in det_list:
            prod_data = item_data.get('prod', {})
            codigo_produto = prod_data.get('cProd')
            if not codigo_produto: continue

            quantidade = Decimal(prod_data.get('qCom', '0'))
            valor_unitario = Decimal(prod_data.get('vUnCom', '0'))

            if codigo_produto not in produtos_agregados:
                produtos_agregados[codigo_produto] = {
                    'quantidade_total': Decimal('0'),
                    'valor_total_ponderado': Decimal('0'),
                    'dados_primeiro_item': prod_data, # Guarda dados para criaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o do produto
                    'item_xml_primeiro': item_data,
                    'categoria_id': categorias_mapeadas.get(codigo_produto)
                }
            
            produtos_agregados[codigo_produto]['quantidade_total'] += quantidade
            produtos_agregados[codigo_produto]['valor_total_ponderado'] += quantidade * valor_unitario

        # 4. SALVAMENTO (ITENS DA NOTA E PRODUTO MESTRE)
        for item_data in det_list:
            prod_data = item_data.get('prod', {})
            codigo_produto = prod_data.get('cProd')
            if not codigo_produto: continue

            # 4.1. Atualiza ou Cria o Produto Mestre
            dados_agregados = produtos_agregados[codigo_produto]
            produto_obj = _update_or_create_produto_mestre(
                codigo_produto, dados_agregados, emitente
            )

            # 4.2. Cria o Item da Nota Fiscal (Fiel ao XML)
            _create_item_nota_fiscal(nf, item_data, produto_obj)
            
            # 4.3. Cria a Entrada de Produto
            entrada_produto_obj = EntradaProduto.objects.create( # Captura o objeto criado
                item_nota_fiscal=ItemNotaFiscal.objects.latest('id'), # Pega o ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âºltimo item criado
                quantidade=Decimal(prod_data.get('qCom', '0')),
                preco_unitario=Decimal(prod_data.get('vUnCom', '0')),
                preco_total=Decimal(prod_data.get('vProd', '0')),
                fornecedor=emitente,
                nota_fiscal=nf,
                numero_nota=nf.numero,
            )
            # 4.4. Recalcula o estoque e preÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§os do Produto mestre
            produto_obj.recalculate_stock_and_prices() # Chama o mÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©todo para recalcular


        # 5. Processar Transporte e Duplicatas
        transp_data = infNFe.get('transp', {})
        if transp_data:
            _create_transporte(nf, transp_data)

        cobr_data = infNFe.get('cobr', {})
        if cobr_data and 'dup' in cobr_data:
            _create_duplicatas(nf, cobr_data.get('dup', []))
            _inferir_condicao_por_cobr(nf, cobr_data)

        print(f"--- Sucesso: Nota Fiscal {nf.numero} (ID: {nf.pk}) salva com sucesso. ---")
        message = app_messages.success_updated(nf) if nota_existente and force_update else app_messages.success_imported(nf, source_type="XML")

        from django.urls import reverse
        return JsonResponse({
            'success': True,
            'message': message,
            'nota_id': nf.pk,
            'redirect_url': reverse('nota_fiscal:entradas_nota')
        }, status=201)

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': app_messages.error(f'Ocorreu um erro inesperado no servidor: {str(e)}')}, status=500)


# --- FunÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âµes de Apoio para `processar_importacao_xml_view` ---

def _get_or_create_empresa(data, tipo):
    """Cria ou obtÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©m uma Empresa a partir dos dados do XML (emitente ou destinatÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡rio)."""
    identificador = data.get('CNPJ') or data.get('CPF')
    if not identificador:
        raise ValueError(f"CNPJ/CPF nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o encontrado para {tipo}")

    identificador_limpo = re.sub(r'\D', '', identificador)
    is_cnpj = len(identificador_limpo) == 14

    lookup_field = 'cnpj' if is_cnpj else 'cpf'
    ender_data = data.get('enderEmit', {}) if tipo == 'emit' else data.get('enderDest', {})

    defaults = {
        'razao_social': data.get('xNome', '') if is_cnpj else '',
        'nome_fantasia': data.get('xFant', '') if is_cnpj else '',
        'nome': data.get('xNome', '') if not is_cnpj else '',
        'tipo_empresa': 'pj' if is_cnpj else 'pf',
        'logradouro': ender_data.get('xLgr', ''),
        'numero': ender_data.get('nro', ''),
        'bairro': ender_data.get('xBairro', ''),
        'cidade': ender_data.get('xMun', ''),
        'uf': ender_data.get('UF', ''),
        'cep': re.sub(r'\D', '', ender_data.get('CEP', '')),
        'ie': data.get('IE', ''),
        'status_empresa': 'ativa',
    }

    empresa, created = Empresa.objects.update_or_create(
        **{lookup_field: identificador_limpo},
        defaults=defaults
    )
    print(f"Empresa ({tipo}) {'criada' if created else 'encontrada'}: {empresa}")
    return empresa


def _to_decimal_safe(value, default='0'):
    try:
        if value in (None, ''):
            return Decimal(default)
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


def _extrair_blocos_imposto(item_data):
    imposto_data = (item_data or {}).get('imposto', {}) or {}
    icms_root = imposto_data.get('ICMS', {}) or {}
    icms_data = next(iter(icms_root.values()), {}) if isinstance(icms_root, dict) and icms_root else {}
    ipi_data = imposto_data.get('IPI', {}).get('IPITrib', {}) or imposto_data.get('IPI', {}).get('IPINT', {}) or {}
    pis_root = imposto_data.get('PIS', {}) or {}
    pis_data = next(iter(pis_root.values()), {}) if isinstance(pis_root, dict) and pis_root else {}
    cofins_root = imposto_data.get('COFINS', {}) or {}
    cofins_data = next(iter(cofins_root.values()), {}) if isinstance(cofins_root, dict) and cofins_root else {}
    return icms_data, ipi_data, pis_data, cofins_data

def _update_or_create_produto_mestre(codigo_produto, dados_agregados, fornecedor):
    """Atualiza ou cria um registro na tabela mestre de Produtos."""
    produto, created = Produto.objects.get_or_create(
        codigo_fornecedor=codigo_produto,
        defaults={
            'nome': dados_agregados['dados_primeiro_item'].get('xProd', ''),
            'fornecedor': fornecedor,
            'controla_estoque': True,
            'ativo': True,
        }
    )

    # Atualiza o estoque
    produto.estoque_atual += dados_agregados['quantidade_total']
    
    # Calcula o novo custo mÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©dio ponderado
    if produto.preco_custo and produto.estoque_atual > dados_agregados['quantidade_total']:
        valor_estoque_antigo = produto.preco_custo * (produto.estoque_atual - dados_agregados['quantidade_total'])
        novo_custo_medio = (valor_estoque_antigo + dados_agregados['valor_total_ponderado']) / produto.estoque_atual
        produto.preco_custo = novo_custo_medio
    else:
        # Se nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o hÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡ estoque anterior, o custo mÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©dio ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© o da nota
        produto.preco_custo = dados_agregados['valor_total_ponderado'] / dados_agregados['quantidade_total']

    # Atualiza a categoria se foi informada
    categoria_id = dados_agregados.get('categoria_id')
    if categoria_id:
        produto.categoria = CategoriaProduto.objects.get(pk=categoria_id)

    produto.save()

    prod_primeiro_item = dados_agregados.get('dados_primeiro_item', {}) or {}
    item_xml = dados_agregados.get('item_xml_primeiro', {}) or {}
    icms_data, ipi_data, pis_data, cofins_data = _extrair_blocos_imposto(item_xml)

    detalhes_fiscais, _ = DetalhesFiscaisProduto.objects.get_or_create(produto=produto)
    changed_fields = []

    ncm_codigo_xml = normalizar_codigo_ncm(prod_primeiro_item.get('NCM'))
    if ncm_codigo_xml:
        ncm_obj, _ = NCM.objects.get_or_create(
            codigo=ncm_codigo_xml,
            defaults={'descricao': f'NCM importado via XML ({ncm_codigo_xml})'}
        )
        if detalhes_fiscais.ncm_id != ncm_obj.id:
            detalhes_fiscais.ncm = ncm_obj
            changed_fields.append('ncm')

    origem_xml = str(icms_data.get('orig') or '').strip()
    if origem_xml in dict(DetalhesFiscaisProduto.ORIGEM_MERCADORIA_CHOICES):
        if (detalhes_fiscais.origem_mercadoria or '') != origem_xml:
            detalhes_fiscais.origem_mercadoria = origem_xml
            changed_fields.append('origem_mercadoria')

    cfop_xml = str(prod_primeiro_item.get('CFOP') or '').strip()
    if cfop_xml and (detalhes_fiscais.cfop or '') != cfop_xml:
        detalhes_fiscais.cfop = cfop_xml
        changed_fields.append('cfop')

    unidade_xml = str(prod_primeiro_item.get('uCom') or '').strip()
    if unidade_xml and (detalhes_fiscais.unidade_comercial or '') != unidade_xml:
        detalhes_fiscais.unidade_comercial = unidade_xml
        changed_fields.append('unidade_comercial')

    quantidade_xml = _to_decimal_safe(prod_primeiro_item.get('qCom'), default='0')
    if quantidade_xml > 0 and detalhes_fiscais.quantidade_comercial != quantidade_xml:
        detalhes_fiscais.quantidade_comercial = quantidade_xml
        changed_fields.append('quantidade_comercial')

    valor_unit_xml = _to_decimal_safe(prod_primeiro_item.get('vUnCom'), default='0')
    if valor_unit_xml > 0 and detalhes_fiscais.valor_unitario_comercial != valor_unit_xml:
        detalhes_fiscais.valor_unitario_comercial = valor_unit_xml
        changed_fields.append('valor_unitario_comercial')

    v_icms = _to_decimal_safe(icms_data.get('vICMS'), default='0')
    if v_icms > 0 and detalhes_fiscais.icms != v_icms:
        detalhes_fiscais.icms = v_icms
        changed_fields.append('icms')

    v_ipi = _to_decimal_safe(ipi_data.get('vIPI'), default='0')
    if v_ipi > 0 and detalhes_fiscais.ipi != v_ipi:
        detalhes_fiscais.ipi = v_ipi
        changed_fields.append('ipi')

    v_pis = _to_decimal_safe(pis_data.get('vPIS'), default='0')
    if v_pis > 0 and detalhes_fiscais.pis != v_pis:
        detalhes_fiscais.pis = v_pis
        changed_fields.append('pis')

    v_cofins = _to_decimal_safe(cofins_data.get('vCOFINS'), default='0')
    if v_cofins > 0 and detalhes_fiscais.cofins != v_cofins:
        detalhes_fiscais.cofins = v_cofins
        changed_fields.append('cofins')

    if changed_fields:
        detalhes_fiscais.save(update_fields=changed_fields)

    print(f"Produto mestre {'criado' if created else 'atualizado'}: {produto.nome}")
    return produto


def _create_item_nota_fiscal(nota_fiscal, item_data, produto_obj):
    """Cria um registro de ItemNotaFiscal fiel aos dados do XML."""
    prod_data = item_data.get('prod', {})
    imposto_data = item_data.get('imposto', {})
    icms_data = imposto_data.get('ICMS', {}).get(next(iter(imposto_data.get('ICMS', {})), None), {})
    ipi_data = imposto_data.get('IPI', {}).get('IPITrib', {}) or imposto_data.get('IPI', {}).get('IPINT', {})
    pis_data = next(iter(imposto_data.get('PIS', {}).values()), {})
    cofins_data = next(iter(imposto_data.get('COFINS', {}).values()), {})

    item = ItemNotaFiscal.objects.create(
        nota_fiscal=nota_fiscal,
        produto=produto_obj,
        codigo=prod_data.get('cProd'),
        descricao=prod_data.get('xProd'),
        ncm=normalizar_codigo_ncm(prod_data.get('NCM')), 
        cfop=prod_data.get('CFOP'),
        unidade=prod_data.get('uCom'),
        quantidade=Decimal(prod_data.get('qCom', '0')),
        valor_unitario=Decimal(prod_data.get('vUnCom', '0')),
        valor_total=Decimal(prod_data.get('vProd', '0')),
        desconto=Decimal(prod_data.get('vDesc', '0')),
        base_calculo_icms=Decimal(icms_data.get('vBC', '0')),
        aliquota_icms=Decimal(icms_data.get('pICMS', '0')),
        # Adicione outros campos de impostos conforme necessÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡rio
    )
    print(f"Item da nota criado: {item.descricao}")
    return item

def _create_transporte(nf, data):
    """Cria o registro de TransporteNotaFiscal."""
    vol = data.get('vol', {})
    if isinstance(vol, list):
        vol = vol[0] if vol else {}

    transporta = data.get('transporta') or {}
    transportadora_nome = (transporta.get('xNome') or '').strip()
    transportadora_cnpj = re.sub(r'\D', '', str(transporta.get('CNPJ') or ''))

    transportadora_obj = None
    if transportadora_cnpj:
        transportadora_obj = Empresa.objects.filter(cnpj=transportadora_cnpj).first()
    if not transportadora_obj and transportadora_nome:
        transportadora_obj = Empresa.objects.filter(razao_social__iexact=transportadora_nome).first() or Empresa.objects.filter(nome__iexact=transportadora_nome).first()
    if not transportadora_obj and (transportadora_nome or transportadora_cnpj):
        categoria_transportadora = CategoriaEmpresa.objects.filter(nome__iexact='Transportadora').first()
        if not categoria_transportadora:
            categoria_transportadora = CategoriaEmpresa.objects.create(nome='Transportadora')
        transportadora_obj = Empresa.objects.create(
            tipo_empresa='pj',
            razao_social=transportadora_nome or f'Transportadora {transportadora_cnpj}',
            nome_fantasia=transportadora_nome or None,
            cnpj=transportadora_cnpj or None,
            categoria=categoria_transportadora,
            fornecedor=True,
            status_empresa='ativa',
        )

    TransporteNotaFiscal.objects.create(
        nota_fiscal=nf,
        transportadora=transportadora_obj,
        modalidade_frete=data.get('modFrete', ''),
        transportadora_nome=transportadora_nome,
        transportadora_cnpj=transportadora_cnpj,
        placa_veiculo=(data.get('veicTransp') or {}).get('placa', ''),
        uf_veiculo=(data.get('veicTransp') or {}).get('UF', ''),
        rntc=(data.get('veicTransp') or {}).get('RNTC', ''),
        quantidade_volumes=int(vol.get('qVol', 0) or 0),
        especie_volumes=vol.get('esp', ''),
        peso_liquido=Decimal(vol.get('pesoL', '0')),
        peso_bruto=Decimal(vol.get('pesoB', '0')),
    )
    print("Dados de transporte salvos.")

def _create_duplicatas(nf, duplicatas_data):
    """Cria os registros de DuplicataNotaFiscal."""
    if not isinstance(duplicatas_data, list):
        duplicatas_data = [duplicatas_data]
        
    for dup_data in duplicatas_data:
        DuplicataNotaFiscal.objects.create(
            nota_fiscal=nf,
            numero=dup_data.get('nDup', ''),
            valor=Decimal(dup_data.get('vDup', '0')),
            vencimento=_parse_datetime(dup_data.get('dVenc'), date_only=True)
        )
    print(f"{len(duplicatas_data)} duplicata(s) salva(s).")


def _inferir_condicao_por_cobr(nf, cobr_data):
    duplicatas_data = (cobr_data or {}).get('dup', [])
    if not duplicatas_data:
        return
    if not isinstance(duplicatas_data, list):
        duplicatas_data = [duplicatas_data]

    base = nf.data_emissao
    if hasattr(base, 'date'):
        base = base.date()
    dias = []
    for dup in duplicatas_data:
        venc = _parse_datetime((dup or {}).get('dVenc'), date_only=True)
        if hasattr(venc, 'date'):
            venc = venc.date()
        if base and venc:
            dias.append(max((venc - base).days, 0))
    if not dias:
        return

    descricao = '/'.join(str(dia) for dia in dias) + ' DDL'
    nf.condicao_pagamento = descricao
    nf.quantidade_parcelas = len(dias)
    nf.save(update_fields=['condicao_pagamento', 'quantidade_parcelas'])

def _parse_datetime(dt_str, date_only=False):
    """Converte string de data/hora ISO para objeto datetime ou date."""
    if not dt_str: return None
    try:
        dt = datetime.datetime.fromisoformat(dt_str)
        return dt.date() if date_only else dt
    except (ValueError, TypeError):
        return None

# --- Views de Listagem e Outras --- #

@login_required_json
@permission_required_json('nota_fiscal.view_notafiscal', raise_exception=True)
@require_GET
def entradas_nota_view(request):
    """Lista as notas fiscais de entrada com opÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o de busca e ordenaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o."""
    termo = request.GET.get('termo', '').strip()
    ordenacao = request.GET.get('ordenacao', '-data_emissao')

    # Usamos select_related para otimizar a busca, trazendo os dados do emitente e destinatÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡rio
    # em uma ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âºnica consulta ao banco de dados.
    qs = NotaFiscal.objects.select_related('emitente', 'destinatario').filter(emitente__isnull=False)

    if termo:
        qs = qs.filter(
            Q(numero__icontains=termo) |
            Q(emitente__razao_social__icontains=termo) |
            Q(emitente__nome__icontains=termo) |
            Q(destinatario__razao_social__icontains=termo) |
            Q(destinatario__nome__icontains=termo) |
            Q(chave_acesso__icontains=termo)
        )

    # Garante que a ordenacao seja valida para evitar erros
    try:
        if ordenacao in ('numero', '-numero'):
            numero_order = 'numero_int' if ordenacao == 'numero' else '-numero_int'
            qs = qs.annotate(numero_int=Cast('numero', IntegerField())).order_by(numero_order, 'numero')
        else:
            qs = qs.order_by(ordenacao)
    except Exception:
        qs = qs.order_by('-data_emissao')

    context = {
        'entradas': qs,  # Passa o queryset diretamente
        'termo': termo,
        'ordenacao_atual': ordenacao,
        'content_template': 'partials/nota_fiscal/entradas_nota.html',
        'data_page': 'entradas_nota',
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, context['content_template'], context)

    return render(request, 'base.html', context)

@login_required_json
@permission_required_json('nota_fiscal.add_notafiscal', raise_exception=True)
@require_GET
def lancar_nota_manual_view(request):
    """
    Renderiza a pÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡gina para lanÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§amento manual de notas fiscais,
    respondendo a requisiÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âµes normais e AJAX.
    """
    categorias = list(CategoriaProduto.objects.order_by("nome").values("id", "nome"))
    empresas = list(Empresa.objects.all().values(
        'id', 'cnpj', 'cpf', 'razao_social', 'nome_fantasia', 'nome',
        'logradouro', 'numero', 'bairro', 'cidade', 'uf', 'cep', 'ie'
    ))
    context = {
        'categorias_disponiveis_json': json.dumps(categorias, ensure_ascii=False),
        'empresas_disponiveis_json': json.dumps(empresas, ensure_ascii=False),
        'content_template': 'partials/nota_fiscal/lancar_nota_manual.html',
        'data_page': 'lancar_nota_manual',
        'data_tela': 'lancar_nota_manual',
    }

    # Se a requisiÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o for AJAX, retorna apenas o template parcial (o "miolo").
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, context['content_template'], context)

    # Para acesso direto via URL, retorna a pÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡gina completa.
    return render(request, 'base.html', context)

# Substitua a sua funÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o editar_nota_view por esta:

def _item_forca_override_manual(item_form):
    cleaned = getattr(item_form, 'cleaned_data', {}) or {}
    if cleaned.get('DELETE'):
        return False
    contexto_raw = cleaned.get('dados_contexto_regra')
    contexto = {}
    if contexto_raw:
        if isinstance(contexto_raw, dict):
            contexto = contexto_raw
        else:
            try:
                contexto = json.loads(contexto_raw)
            except Exception:
                contexto = {}
    if bool(contexto.get('manual_override')):
        return True
    origem = (cleaned.get('aliquota_icms_origem') or '').strip().lower()
    regra_aplicada = cleaned.get('regra_icms_aplicada')
    return origem == 'manual' and bool(regra_aplicada)
@login_required_json
@permission_required_json('nota_fiscal.change_notafiscal', raise_exception=True)
@require_http_methods(["GET", "POST"])
@transaction.atomic
def editar_nota_view(request, pk):
    """
    Lida com a criacao (GET) e o processamento (POST) do formulario de edicao de Nota Fiscal,
    respondendo a requisicoes normais e AJAX para a exibicao do formulario.
    """
    app_messages = get_app_messages(request)
    nota = get_object_or_404(NotaFiscal, pk=pk)
    if _nota_saida_fora_emitente_ativo(request, nota):
        message = app_messages.error('A nota fiscal nao pertence a empresa ativa.')
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': message, 'code': 'permission_denied'}, status=403)
        messages.error(request, message)
        return redirect('nota_fiscal:emitir_nfe_list')
    if request.method == 'POST':
        if request.POST.get('action') == 'delete_nota':
            status = (nota.status_sefaz or '').strip().lower()
            allowed_delete_status = {'', 'rascunho', 'erro_rejeicao'}
            if status not in allowed_delete_status:
                app_messages.error('Somente notas em rascunho/nao emitidas podem ser excluidas.')
            else:
                numero_nota = nota.numero
                tipo_operacao = nota.tipo_operacao
                nota.delete()
                app_messages.success_deleted('nota fiscal', f'N? {numero_nota}')
                if tipo_operacao == '1':
                    return redirect('nota_fiscal:emitir_nfe_list')
                return redirect('nota_fiscal:entradas_nota')
        post_data = request.POST.copy()
        is_saida = str(nota.tipo_operacao or '') == '1'
        emitente_id = None
        if is_saida:
            emitente_id = (post_data.get('emitente_proprio') or '').strip() or None
            if emitente_id:
                post_data['emitente_proprio'] = ''
            form = NotaFiscalForm(post_data, instance=nota)
        else:
            if not (post_data.get('tipo_operacao') or '').strip():
                post_data['tipo_operacao'] = '0'
            form = NotaFiscalEntradaForm(post_data, instance=nota)
        item_formset = ItemNotaFiscalFormSet(request.POST, instance=nota, prefix='items')
        duplicata_formset = DuplicataNotaFiscalFormSet(request.POST, instance=nota, prefix='duplicatas')
        transporte_formset = TransporteNotaFiscalFormSet(request.POST, instance=nota, prefix='transporte')
        if form.is_valid() and item_formset.is_valid() and duplicata_formset.is_valid() and transporte_formset.is_valid():
            if any(_item_forca_override_manual(item_form) for item_form in item_formset.forms):
                if not request.user.has_perm('fiscal_regras.override_aliquota_item'):
                    form.add_error(None, 'Voce nao tem permissao para sobrescrever aliquota automatica de ICMS.')
                    app_messages.error('Permissao insuficiente para override manual de aliquota.')
                else:
                    for item_form in item_formset.forms:
                        if _item_forca_override_manual(item_form):
                            cleaned = getattr(item_form, 'cleaned_data', {}) or {}
                            contexto_raw = cleaned.get('dados_contexto_regra')
                            contexto = {}
                            if contexto_raw:
                                if isinstance(contexto_raw, dict):
                                    contexto = contexto_raw
                                else:
                                    try:
                                        contexto = json.loads(contexto_raw)
                                    except Exception:
                                        contexto = {}
                            contexto['manual_override'] = True
                            cleaned['dados_contexto_regra'] = json.dumps(contexto, ensure_ascii=False)
            if form.errors or item_formset.non_form_errors():
                app_messages.error('Foram encontrados erros no formulario. Por favor, corrija-os.')
            else:
                nota_salva = form.save(commit=False)
                if is_saida and emitente_id:
                    nota_salva.emitente_proprio_id = int(emitente_id)
                if not is_saida and not (nota_salva.tipo_operacao or '').strip():
                    nota_salva.tipo_operacao = '0'
                nota_salva.save()
                item_formset.save()
                duplicata_formset.save()
                _sincronizar_duplicatas_nota(nota_salva)
                transporte_formset.save()
                app_messages.success_updated(nota)
                if nota.tipo_operacao == '1':
                    return redirect('nota_fiscal:emitir_nfe_list')
                return redirect('nota_fiscal:entradas_nota')
        else:
            app_messages.error('Foram encontrados erros no formulario. Por favor, corrija-os.')
    is_saida = str(nota.tipo_operacao or '') == '1'
    form = NotaFiscalForm(instance=nota) if is_saida else NotaFiscalEntradaForm(instance=nota)
    item_formset = ItemNotaFiscalFormSet(instance=nota, prefix='items')
    duplicata_formset = DuplicataNotaFiscalFormSet(instance=nota, prefix='duplicatas')
    transporte_formset = TransporteNotaFiscalFormSet(instance=nota, prefix='transporte')
    context = {
        'nota': nota,
        'form': form,
        'item_formset': item_formset,
        'duplicata_formset': duplicata_formset,
        'transporte_formset': transporte_formset,
        'content_template': 'partials/nota_fiscal/editar_nota.html',
        'data_page': 'editar_nota',
        'data_tela': 'editar_nota',
    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, context['content_template'], context)
    return render(request, 'base.html', context)

@login_required_json
@permission_required_json('nota_fiscal.delete_notafiscal', raise_exception=True)
@require_POST
@transaction.atomic
def excluir_notas_multiplo_view(request):
    app_messages = get_app_messages(request)
    """
    Exclui mÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âºltiplas notas fiscais com base nos IDs recebidos via POST.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        ids = data.get('ids', [])

        if not ids:
            message = app_messages.error('Nenhum ID fornecido para exclusÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o.')
            return JsonResponse({'success': False, 'message': message}, status=400)

        emitente_ativo_id = _get_emitente_ativo_id(request)
        if emitente_ativo_id:
            ids_nao_autorizados = list(
                NotaFiscal.objects.filter(id__in=ids, tipo_operacao='1')
                .exclude(emitente_proprio_id=emitente_ativo_id)
                .values_list('id', flat=True)
            )
            if ids_nao_autorizados:
                message = app_messages.error('Ha notas de saida fora da empresa ativa na selecao.')
                return JsonResponse(
                    {'success': False, 'message': message, 'code': 'permission_denied', 'ids': ids_nao_autorizados},
                    status=403
                )

        notas_excluidas, _ = NotaFiscal.objects.filter(id__in=ids).delete()

        if notas_excluidas > 0:
            message = app_messages.success_deleted("nota(s) fiscal(is)", f"{notas_excluidas} selecionada(s)")
            return JsonResponse({'success': True, 'message': message})
        else:
            message = app_messages.error('Nenhuma nota fiscal encontrada com os IDs fornecidos.')
            return JsonResponse({'success': False, 'message': message}, status=404)

    except json.JSONDecodeError:
        message = app_messages.error('RequisiÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o invÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡lida. JSON malformado.')
        return JsonResponse({'success': False, 'message': message}, status=400)
    except Exception as e:
        traceback.print_exc()
        message = app_messages.error(f'Erro ao excluir notas fiscais: {str(e)}')
        return JsonResponse({'success': False, 'message': message}, status=500)


@login_required_json
@permission_required_json('nota_fiscal.view_notafiscal', raise_exception=True)
@require_GET
def buscar_produtos_para_nota_view(request):
    """
    Busca produtos para adicionar a uma nota fiscal manual, retornando JSON.
    """
    termo = request.GET.get('q', '').strip()
    by = (request.GET.get('by') or '').strip().lower()

    if by == 'code':
        produtos = Produto.objects.filter(
            Q(codigo_interno__icontains=termo) | Q(codigo_fornecedor__icontains=termo)
        )
    elif by == 'name':
        produtos = Produto.objects.filter(
            Q(nome__icontains=termo)
        )
    else:
        produtos = Produto.objects.filter(
            Q(nome__icontains=termo)
            | Q(codigo_interno__icontains=termo)
            | Q(codigo_fornecedor__icontains=termo)
        )

    produtos = produtos.select_related('unidade_medida_interna')[:50] # Limita a 50 resultados

    resultados = []
    for p in produtos:
        try:
            detalhes_fiscais = p.detalhes_fiscais
        except Exception:
            detalhes_fiscais = None

        ncm_codigo = ''
        cfop_codigo = ''
        if detalhes_fiscais:
            if detalhes_fiscais.ncm:
                ncm_codigo = formatar_codigo_ncm(detalhes_fiscais.ncm.codigo)
            cfop_codigo = detalhes_fiscais.cfop or ''

        resultados.append({
            'id': p.id,
            'text': f"{p.codigo_interno} - {p.nome}",
            'codigo_interno': p.codigo_interno,
            'codigo_fornecedor': p.codigo_fornecedor,
            'nome': p.nome,
            'descricao_item': p.nome,
            'unidade': p.unidade_medida_interna.sigla if p.unidade_medida_interna else 'UN',
            'preco_venda': p.preco_venda,
            'ncm': ncm_codigo,
            'cfop': cfop_codigo,
            'origem_mercadoria': detalhes_fiscais.origem_mercadoria if detalhes_fiscais else '',
        })

    return JsonResponse({'results': resultados})


@login_required_json
@permission_required_json('nota_fiscal.view_notafiscal', raise_exception=True)
@require_GET
def resolver_aliquota_item_view(request):
    data_emissao = converter_data_para_date((request.GET.get('data_emissao') or '').strip())

    try:
        resolucao = resolver_regra_icms_item(
            data_emissao=data_emissao,
            emitente_id=request.GET.get('emitente_id') or None,
            destinatario_id=request.GET.get('destinatario_id') or None,
            uf_emitente=request.GET.get('uf_emitente') or None,
            uf_destino=request.GET.get('uf_destino') or None,
            ncm=request.GET.get('ncm') or None,
            tipo_operacao=(request.GET.get('tipo_operacao') or '1').strip(),
            origem_mercadoria=request.GET.get('origem_mercadoria') or None,
            produto_id=request.GET.get('produto_id') or None,
        )
    except DatabaseError:
        return JsonResponse({
            'success': True,
            'found': False,
            'origem': 'manual',
            'aliquota_icms': '0',
            'aliquota_ipi': '',
            'aliquota_pis': '',
            'aliquota_cofins': '',
            'reducao_base_icms': '0',
            'fcp': '0',
            'regra_id': None,
            'regra_descricao': 'Motor fiscal indisponivel. Verifique se as migrations do modulo fiscal_regras foram aplicadas.',
            'contexto': {'motor_versao': 'fiscal_regras_v1'},
        })

    return JsonResponse({
        'success': True,
        'found': resolucao.found,
        'origem': resolucao.origem,
        'aliquota_icms': str(resolucao.aliquota_icms),
        'aliquota_ipi': str(resolucao.aliquota_ipi) if resolucao.aliquota_ipi is not None else '',
        'aliquota_pis': str(resolucao.aliquota_pis) if resolucao.aliquota_pis is not None else '',
        'aliquota_cofins': str(resolucao.aliquota_cofins) if resolucao.aliquota_cofins is not None else '',
        'reducao_base_icms': str(resolucao.reducao_base_icms),
        'fcp': str(resolucao.fcp),
        'regra_id': resolucao.regra_id,
        'regra_descricao': resolucao.regra_descricao,
        'contexto': resolucao.contexto,
    })



# ==============================================================================
# ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â°ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¡ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ VIEW PARA CRIAR NOTA FISCAL DE SAIDA
# ==============================================================================
@login_required_json
@permission_required_json('nota_fiscal.add_notafiscal', raise_exception=True)
def criar_nfe_saida(request):
    """
    Renderiza o formulÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡rio para criar uma nova Nota Fiscal de SaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â­da e processa a sua submissÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o.
    """
    if request.method == 'POST':
        form = NotaFiscalSaidaForm(request.POST)
        if form.is_valid():
            # AINDA NAO SALVA OS ITENS, apenas o cabecalho da nota
            nova_nota = form.save(commit=False)
            nova_nota.created_by = request.user
            nova_nota.tipo_operacao = '1'

            tenant = getattr(request, 'tenant', None)
            emitente_ativo_id = getattr(tenant, 'emitente_padrao_id', None)
            if not emitente_ativo_id:
                emitente_ativo_id = Emitente.objects.filter(is_default=True).values_list('id', flat=True).first()
            if not emitente_ativo_id:
                emitente_ativo_id = getattr(nova_nota, 'emitente_proprio_id', None)

            if not emitente_ativo_id:
                return JsonResponse(
                    {
                        'success': False,
                        'errors': {'emitente_proprio': ['Nenhuma empresa ativa definida para emissao.']}
                    },
                    status=400
                )

            nova_nota.emitente_proprio_id = emitente_ativo_id
            # Gerar nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âºmero e chave de acesso provisÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â³rios
            nova_nota.numero = str(NotaFiscal.objects.count() + 1).zfill(9)
            nova_nota.chave_acesso = f"TEMP-{timezone.now().strftime('%Y%m%d%H%M%S')}-{nova_nota.numero}"
            if not (nova_nota.modelo_documento or '').strip():
                nova_nota.modelo_documento = '55'
            if not (nova_nota.ambiente or '').strip():
                nova_nota.ambiente = '2' if settings.DEBUG else '1'
            nova_nota.save()
            
            messages.success(request, f"Nota Fiscal de SaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â­da NÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Âº {nova_nota.numero} criada com sucesso. Adicione os itens.")
            # Redireciona para a tela de ediÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o para adicionar itens
            return JsonResponse({'success': True, 'redirect_url': reverse('nota_fiscal:editar_nota', kwargs={'pk': nova_nota.pk})})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    else:
        form = NotaFiscalSaidaForm()

    context = {
        'form': form,
        'content_template': 'partials/nota_fiscal/form_nfe_saida.html',
        'data_page': 'criar_nfe_saida',
    }
    return render_ajax_or_base(request, context['content_template'], context)



@login_required_json
@permission_required_json('nota_fiscal.view_notafiscal', raise_exception=True)
@require_GET
def buscar_naturezas_operacao_view(request):
    """Busca naturezas de operacao para autocomplete da NF-e de saida."""
    termo = (request.GET.get('term', '') or request.GET.get('search', '')).strip()
    resultados = []

    if termo:
        qs = NaturezaOperacao.objects.filter(
            Q(codigo__icontains=termo) | Q(descricao__icontains=termo) | Q(observacoes__icontains=termo)
        ).only('codigo', 'descricao').order_by('descricao')[:20]

        for natureza in qs:
            codigo = (natureza.codigo or '').strip()
            descricao = (natureza.descricao or '').strip()
            texto = f"{codigo} - {descricao}" if codigo else descricao
            resultados.append({
                'id': codigo or descricao,
                'codigo': codigo,
                'descricao': descricao,
                'text': texto,
                'valor_gravacao': texto,
            })

    return JsonResponse({'results': resultados})



