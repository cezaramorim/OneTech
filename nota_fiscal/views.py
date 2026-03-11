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
from accounts.utils.decorators import login_required_json
from accounts.utils.decorators import login_required_json
from django.core.files.storage import default_storage
from django.db import transaction, DatabaseError
from django.db.models import Q, IntegerField
from django.db.models.functions import Cast
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.text import slugify
# Removido o @csrf_exempt por razÃƒÆ’Ã‚Âµes de seguranÃƒÆ’Ã‚Â§a
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

# --- FunÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Âµes Auxiliares de Parsing --- #

def strip_namespace(tag):
    """Remove o namespace (ex: {http://...}) de uma tag XML."""
    return tag.split('}')[-1]

def xml_to_dict(element):
    """Converte um elemento XML e seus filhos em um dicionÃƒÆ’Ã‚Â¡rio, tratando namespaces."""
    result = {strip_namespace(element.tag): {}}
    
    # Adiciona atributos do elemento
    if element.attrib:
        result[strip_namespace(element.tag)].update(element.attrib)

    # Adiciona filhos
    for child in element:
        child_dict = xml_to_dict(child)
        child_tag = strip_namespace(child.tag)

        # Se a tag jÃƒÆ’Ã‚Â¡ existe, transforma em lista para agrupar mÃƒÆ’Ã‚Âºltiplos elementos
        if child_tag in result[strip_namespace(element.tag)]:
            if not isinstance(result[strip_namespace(element.tag)][child_tag], list):
                result[strip_namespace(element.tag)][child_tag] = [result[strip_namespace(element.tag)][child_tag]]
            result[strip_namespace(element.tag)][child_tag].append(child_dict[child_tag])
        else:
            result[strip_namespace(element.tag)].update(child_dict)

    # Adiciona o texto do elemento, se houver
    if element.text and element.text.strip():
        text = element.text.strip()
        # Se jÃƒÆ’Ã‚Â¡ houver filhos, adiciona o texto como uma chave especial
        if len(result[strip_namespace(element.tag)]) > 0:
            result[strip_namespace(element.tag)]['#text'] = text
        # SenÃƒÆ’Ã‚Â£o, o valor da tag ÃƒÆ’Ã‚Â© apenas o texto
        else:
            result[strip_namespace(element.tag)] = text
            
    return result

# --- Views Principais --- #

@login_required_json
@require_GET
def emitir_nfe_list_view(request):
    """
    Lista as notas fiscais que estÃƒÆ’Ã‚Â£o prontas para serem emitidas (status em branco ou 'rascunho').
    """
    # Filtra notas do emitente que ÃƒÆ’Ã‚Â© o tenant atual e que ainda nÃƒÆ’Ã‚Â£o foram enviadas.
    # O status pode ser '' (vazio) ou um status especÃƒÆ’Ã‚Â­fico como 'rascunho'.
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
@require_GET
def importar_xml_view(request):
    """Renderiza a pÃƒÆ’Ã‚Â¡gina de upload de XML para importaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o de notas fiscais."""
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
    Recebe um arquivo XML, faz o parsing e retorna um JSON estruturado para o frontend
    exibir o preview da nota e gerenciar a revisÃƒÆ’Ã‚Â£o de itens, incluindo aviso de duplicidade.
    """
    app_messages = get_app_messages(request)
    print("--- Iniciando importaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o e parsing de XML ---")    
    print(f"DEBUG: ConteÃƒÆ’Ã‚Âºdo de request.FILES: {request.FILES}")
    
    xml_file = request.FILES.get('xml')
    
    if xml_file:
        print(f"DEBUG: xml_file encontrado. Tipo: {type(xml_file)}")
        print(f"DEBUG: Nome do arquivo original: '{xml_file.name}'")
        print(f"DEBUG: Nome do arquivo em minÃƒÆ’Ã‚Âºsculas e sem espaÃƒÆ’Ã‚Â§os: '{xml_file.name.lower().strip()}'")
        is_xml_file = xml_file.name.lower().strip().endswith('.xml')
        print(f"DEBUG: Resultado de .endswith('.xml'): {is_xml_file}")
    else:
        print("DEBUG: Nenhum arquivo XML encontrado em request.FILES.get('xml').")
        
    # 1. VerificaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o de PermissÃƒÆ’Ã‚Â£o do UsuÃƒÆ’Ã‚Â¡rio
    if not request.user.has_perm('nota_fiscal.can_import_xml'):
        message = app_messages.error('VocÃƒÆ’Ã‚Âª nÃƒÆ’Ã‚Â£o tem permissÃƒÆ’Ã‚Â£o para importar XML de Notas Fiscais.')
        return JsonResponse({'success': False, 'message': message}, status=403)

    if not xml_file or not xml_file.name.lower().strip().endswith('.xml'):
        print(f"DEBUG: CondiÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o de arquivo XML invÃƒÆ’Ã‚Â¡lido acionada. xml_file is None: {xml_file is None}")
        if xml_file:
            print(f"DEBUG: xml_file.name.lower().strip().endswith('.xml'): {xml_file.name.lower().strip().endswith('.xml')}")
        message = app_messages.error('Arquivo XML invÃƒÆ’Ã‚Â¡lido ou nÃƒÆ’Ã‚Â£o fornecido.')
        return JsonResponse({'success': False, 'message': message}, status=400)

    try:
        # 2. Parsing do XML
        print("DEBUG: Tentando parsear o arquivo XML...")
        tree = ET.parse(xml_file)
        root = tree.getroot()
        print(f"DEBUG: XML parseado com sucesso. Root tag: {root.tag}")
        
        # Usa a funÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o xml_to_dict (element_to_dict de utils.py) para parsear o XML completo
        full_xml_dict = xml_to_dict(root).get('nfeProc', {})
        print(f"DEBUG: ConteÃƒÆ’Ã‚Âºdo de full_xml_dict (primeiros 200 chars): {str(full_xml_dict)[:200]}...")

        infNFe = full_xml_dict.get('NFe', {}).get('infNFe', {})
        if not infNFe:
            print("ERRO: Estrutura do XML invÃƒÆ’Ã‚Â¡lida: <infNFe> nÃƒÆ’Ã‚Â£o encontrado.")
            message = app_messages.error('Estrutura do XML invÃƒÆ’Ã‚Â¡lida: <infNFe> nÃƒÆ’Ã‚Â£o encontrado.')
            return JsonResponse({'success': False, 'message': message}, status=400)
        print("DEBUG: <infNFe> encontrado no XML.")

        # 3. ExtraÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o da Chave de Acesso e VerificaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o de Duplicidade
        chave = infNFe.get('Id', '').replace('NFe', '')
        
        if not chave:
            print("ERRO: NÃƒÆ’Ã‚Â£o foi possÃƒÆ’Ã‚Â­vel extrair a chave de acesso do XML.")
            message = app_messages.error('NÃƒÆ’Ã‚Â£o foi possÃƒÆ’Ã‚Â­vel extrair a chave de acesso do XML.')
            return JsonResponse({'success': False, 'message': message}, status=400)
        print(f"DEBUG: Chave de acesso extraÃƒÆ’Ã‚Â­da: {chave}")

        is_duplicate = False
        if NotaFiscal.objects.filter(chave_acesso=chave).exists():
            is_duplicate = True
            print(f"--- Nota Fiscal com a chave de acesso {chave} jÃƒÆ’Ã‚Â¡ existe no sistema. (Detectado como duplicata) ---")

        # ExtraÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o de dados principais para o preview
        ide = infNFe.get('ide', {})
        emit = infNFe.get('emit', {}) # Obter dados do emitente
        total = infNFe.get('total', {}).get('ICMSTot', {})
        print(f"DEBUG: Dados IDE: {ide.get('nNF', 'N/A')}, Total NF: {total.get('vNF', 'N/A')}")

        # Extrair a razÃƒÆ’Ã‚Â£o social do emitente
        nome_razao_social_emitente = emit.get('xNome', 'Nome do Emitente NÃƒÆ’Ã‚Â£o Encontrado')
        print(f"DEBUG: Nome/RazÃƒÆ’Ã‚Â£o Social do Emitente: {nome_razao_social_emitente}") # Adicionado para depuraÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o
        
        # 4. Montagem da Lista de Produtos e Itens para RevisÃƒÆ’Ã‚Â£o
        produtos_lista = []
        itens_para_revisar = []
        det_list = infNFe.get('det', [])
        if not isinstance(det_list, list):
            det_list = [det_list]
        
        if not isinstance(det_list, list):
            det_list = [det_list]
        print(f"DEBUG: Encontrados {len(det_list)} item(s) na nota.")

        for det_item in det_list:
            prod = det_item.get('prod', {})
            codigo_importado = prod.get('cProd', '')

            produto_existente = Produto.objects.filter(codigo_fornecedor=codigo_importado).first()
            estoque_atual = produto_existente.estoque_atual if produto_existente else 0
            
            produto_data = {
                'nItem': det_item.get('@nItem', ''),
                'codigo': codigo_importado,
                'nome': prod.get('xProd', ''),
                'ncm': formatar_codigo_ncm(prod.get('NCM', '')), 
                'cfop': prod.get('CFOP', ''),
                'quantidade': Decimal(prod.get('qCom', '0')),
                'unidade': prod.get('uCom', ''),
                'valor_unitario': Decimal(prod.get('vUnCom', '0')),
                'valor_total': Decimal(prod.get('vProd', '0')),
                'desconto': Decimal(prod.get('vDesc', '0')),
                'novo': not produto_existente,
                'categoria_id': None,
                'imposto_detalhes': det_item.get('imposto', {}),
                'estoque_atual': estoque_atual,
                'cest': prod.get('CEST', ''),
            }
            produtos_lista.append(produto_data)

            if not produto_existente:
                itens_para_revisar.append({
                    'nItem': produto_data['nItem'],
                    'codigo_produto': produto_data['codigo'],
                    'descricao_produto': produto_data['nome'],
                    'ncm': produto_data['ncm'],
                })
        print(f"DEBUG: {len(itens_para_revisar)} produto(s) precisam de revisÃƒÆ’Ã‚Â£o.")
        
        # 5. Montagem da Resposta JSON para o Frontend
        message = 'XML processado com sucesso! Verifique os itens para revisÃƒÆ’Ã‚Â£o de categoria, se houver.'
        if is_duplicate:
            message = f'Esta Nota Fiscal (Chave: {chave}) jÃƒÆ’Ã‚Â¡ existe no sistema. Deseja importÃƒÆ’Ã‚Â¡-la novamente e atualizar os dados existentes?'

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
            'nome_razao_social': nome_razao_social_emitente, # <-- ADICIONADO AQUI!
        }
        
        print("--- Parsing de XML concluÃƒÆ’Ã‚Â­do com sucesso ---")
        response = JsonResponse(response_payload_for_frontend, encoder=CustomDecimalEncoder)
        print(f"DEBUG: Content-Type da resposta: {response['Content-Type']}")
        return response

    except Exception as e:
        print(f"ERRO CRÃƒÆ’Ã‚ÂTICO em importar_xml_nfe_view: {type(e).__name__} - {e}")
        full_traceback = traceback.format_exc()
        print(f"TRACEBACK COMPLETO:\n{full_traceback}") 
        message = app_messages.error(f'Ocorreu um erro no servidor ao processar o XML: {str(e)}')
        return JsonResponse({'success': False, 'message': message}, status=500)
@login_required_json
# @csrf_exempt REMOVIDO: `require_POST` jÃƒÆ’Ã‚Â¡ garante a proteÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o CSRF adequada para POST requests.
@require_POST
@transaction.atomic # Garante que todas as operaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Âµes de banco de dados sejam atÃƒÆ’Ã‚Â´micas
def processar_importacao_xml_view(request):
    app_messages = get_app_messages(request)
    """
    View unificada que recebe o JSON da nota (com categorias dos produtos jÃƒÆ’Ã‚Â¡ definidas),
    valida e salva a nota fiscal e todos os seus dados relacionados (empresas, produtos, itens, etc.)
    em uma ÃƒÆ’Ã‚Âºnica transaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o.
    """
    print("--- Iniciando processamento e salvamento da importaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o ---")
    try:
        payload = json.loads(request.body.decode('utf-8'))
        chave = payload.get('chave_acesso')
        force_update = payload.get('force_update', False)
        raw_payload = payload.get('raw_payload', {})

        if not chave or not raw_payload:
            return JsonResponse({'success': False, 'message': app_messages.error('Dados essenciais (chave de acesso ou payload) nÃƒÆ’Ã‚Â£o encontrados.')}, status=400)

        infNFe = raw_payload.get('NFe', {}).get('infNFe', {})
        if not infNFe:
            return JsonResponse({'success': False, 'message': app_messages.error('Estrutura do XML invÃƒÆ’Ã‚Â¡lida: <infNFe> nÃƒÆ’Ã‚Â£o encontrado no raw_payload.')}, status=400)

        # Verifica se a nota fiscal jÃƒÆ’Ã‚Â¡ existe
        nota_existente = NotaFiscal.objects.filter(chave_acesso=chave).first()
        if nota_existente:
            if not force_update:
                message = app_messages.warning(f'A Nota Fiscal "{nota_existente.numero}" jÃƒÆ’Ã‚Â¡ foi importada. Deseja substituir os dados existentes?')
                return JsonResponse({
                    'success': True, 'message': message, 'nota_existente': True,
                    'nota_id': nota_existente.pk, 'redirect_url': reverse('nota_fiscal:entradas_nota')
                }, status=200)
            else:
                print(f"--- Excluindo nota fiscal existente (ID: {nota_existente.pk}) para atualizaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o ---")
                nota_existente.delete()

        # 1. Processar Empresas (Emitente e DestinatÃƒÆ’Ã‚Â¡rio)
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
            modelo_documento=(ide.get('mod') or None),
            ambiente=(ide.get('tpAmb') or None),
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

        # Mapeamento de cÃƒÆ’Ã‚Â³digo de produto para categoria para acesso rÃƒÆ’Ã‚Â¡pido
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
                    'dados_primeiro_item': prod_data, # Guarda dados para criaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o do produto
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
                item_nota_fiscal=ItemNotaFiscal.objects.latest('id'), # Pega o ÃƒÆ’Ã‚Âºltimo item criado
                quantidade=Decimal(prod_data.get('qCom', '0')),
                preco_unitario=Decimal(prod_data.get('vUnCom', '0')),
                preco_total=Decimal(prod_data.get('vProd', '0')),
                fornecedor=emitente,
                nota_fiscal=nf,
                numero_nota=nf.numero,
            )
            # 4.4. Recalcula o estoque e preÃƒÆ’Ã‚Â§os do Produto mestre
            produto_obj.recalculate_stock_and_prices() # Chama o mÃƒÆ’Ã‚Â©todo para recalcular


        # 5. Processar Transporte e Duplicatas
        transp_data = infNFe.get('transp', {})
        if transp_data:
            _create_transporte(nf, transp_data)

        cobr_data = infNFe.get('cobr', {})
        if cobr_data and 'dup' in cobr_data:
            _create_duplicatas(nf, cobr_data.get('dup', []))

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


# --- FunÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Âµes de Apoio para `processar_importacao_xml_view` ---

def _get_or_create_empresa(data, tipo):
    """Cria ou obtÃƒÆ’Ã‚Â©m uma Empresa a partir dos dados do XML (emitente ou destinatÃƒÆ’Ã‚Â¡rio)."""
    identificador = data.get('CNPJ') or data.get('CPF')
    if not identificador:
        raise ValueError(f"CNPJ/CPF nÃƒÆ’Ã‚Â£o encontrado para {tipo}")

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
    
    # Calcula o novo custo mÃƒÆ’Ã‚Â©dio ponderado
    if produto.preco_custo and produto.estoque_atual > dados_agregados['quantidade_total']:
        valor_estoque_antigo = produto.preco_custo * (produto.estoque_atual - dados_agregados['quantidade_total'])
        novo_custo_medio = (valor_estoque_antigo + dados_agregados['valor_total_ponderado']) / produto.estoque_atual
        produto.preco_custo = novo_custo_medio
    else:
        # Se nÃƒÆ’Ã‚Â£o hÃƒÆ’Ã‚Â¡ estoque anterior, o custo mÃƒÆ’Ã‚Â©dio ÃƒÆ’Ã‚Â© o da nota
        produto.preco_custo = dados_agregados['valor_total_ponderado'] / dados_agregados['quantidade_total']

    # Atualiza a categoria se foi informada
    categoria_id = dados_agregados.get('categoria_id')
    if categoria_id:
        produto.categoria = CategoriaProduto.objects.get(pk=categoria_id)

    produto.save()
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
        # Adicione outros campos de impostos conforme necessÃƒÆ’Ã‚Â¡rio
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
@require_GET
def entradas_nota_view(request):
    """Lista as notas fiscais de entrada com opÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o de busca e ordenaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o."""
    termo = request.GET.get('termo', '').strip()
    ordenacao = request.GET.get('ordenacao', '-data_emissao')

    # Usamos select_related para otimizar a busca, trazendo os dados do emitente e destinatÃƒÆ’Ã‚Â¡rio
    # em uma ÃƒÆ’Ã‚Âºnica consulta ao banco de dados.
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
@require_GET
def lancar_nota_manual_view(request):
    """
    Renderiza a pÃƒÆ’Ã‚Â¡gina para lanÃƒÆ’Ã‚Â§amento manual de notas fiscais,
    respondendo a requisiÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Âµes normais e AJAX.
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

    # Se a requisiÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o for AJAX, retorna apenas o template parcial (o "miolo").
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, context['content_template'], context)

    # Para acesso direto via URL, retorna a pÃƒÆ’Ã‚Â¡gina completa.
    return render(request, 'base.html', context)

# Substitua a sua funÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o editar_nota_view por esta:

@login_required_json
@require_http_methods(["GET", "POST"] )
@transaction.atomic
def editar_nota_view(request, pk):
    """
    Lida com a criaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o (GET) e o processamento (POST) do formulÃƒÆ’Ã‚Â¡rio de ediÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o de Nota Fiscal,
    respondendo a requisiÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Âµes normais e AJAX para a exibiÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o do formulÃƒÆ’Ã‚Â¡rio.
    """
    app_messages = get_app_messages(request)
    nota = get_object_or_404(NotaFiscal, pk=pk)

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
            nota_salva = form.save(commit=False)
            if is_saida and emitente_id:
                nota_salva.emitente_proprio_id = int(emitente_id)
            if not is_saida and not (nota_salva.tipo_operacao or '').strip():
                nota_salva.tipo_operacao = '0'
            nota_salva.save()
            item_formset.save()
            duplicata_formset.save()
            # Sincroniza quantidade final de duplicatas com a quantidade de parcelas da condicao selecionada.
            # Isso evita manter parcelas antigas quando a condicao muda para menos vencimentos (ex.: 3 -> 1).
            parcelas_desejadas = max(int(nota_salva.quantidade_parcelas or 1), 1)
            duplicatas_atuais = list(nota_salva.duplicatas.order_by('id'))

            if len(duplicatas_atuais) > parcelas_desejadas:
                ids_excedentes = [dup.id for dup in duplicatas_atuais[parcelas_desejadas:]]
                DuplicataNotaFiscal.objects.filter(id__in=ids_excedentes).delete()
                duplicatas_atuais = duplicatas_atuais[:parcelas_desejadas]

            if len(duplicatas_atuais) < parcelas_desejadas:
                base_date = nota_salva.data_emissao or timezone.localdate()
                faltantes = parcelas_desejadas - len(duplicatas_atuais)
                for idx in range(faltantes):
                    numero_seq = len(duplicatas_atuais) + idx + 1
                    DuplicataNotaFiscal.objects.create(
                        nota_fiscal=nota_salva,
                        numero=str(numero_seq).zfill(3),
                        vencimento=base_date + datetime.timedelta(days=((numero_seq - 1) * 30)),
                        valor=Decimal('0.00'),
                    )
            transporte_formset.save()
            
            app_messages.success_updated(nota)
            if nota.tipo_operacao == '1':
                return redirect('nota_fiscal:emitir_nfe_list')
            return redirect('nota_fiscal:entradas_nota')
        else:
            app_messages.error("Foram encontrados erros no formulÃƒÆ’Ã‚Â¡rio. Por favor, corrija-os.")
            # A lÃƒÆ’Ã‚Â³gica de printar erros para debug pode ser mantida aqui...
            
    # A lÃƒÆ’Ã‚Â³gica para GET comeÃƒÆ’Ã‚Â§a aqui
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

    # Se a requisiÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o for AJAX (vinda de um clique em 'Editar' na lista),
    # renderiza apenas o template parcial.
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, context['content_template'], context)

    # Para acesso direto via URL ou em caso de erro no POST, renderiza a pÃƒÆ’Ã‚Â¡gina completa.
    return render(request, 'base.html', context)

@login_required_json
@require_POST
@transaction.atomic
def excluir_notas_multiplo_view(request):
    app_messages = get_app_messages(request)
    """
    Exclui mÃƒÆ’Ã‚Âºltiplas notas fiscais com base nos IDs recebidos via POST.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        ids = data.get('ids', [])

        if not ids:
            message = app_messages.error('Nenhum ID fornecido para exclusÃƒÆ’Ã‚Â£o.')
            return JsonResponse({'success': False, 'message': message}, status=400)

        notas_excluidas, _ = NotaFiscal.objects.filter(id__in=ids).delete()

        if notas_excluidas > 0:
            message = app_messages.success_deleted("nota(s) fiscal(is)", f"{notas_excluidas} selecionada(s)")
            return JsonResponse({'success': True, 'message': message})
        else:
            message = app_messages.error('Nenhuma nota fiscal encontrada com os IDs fornecidos.')
            return JsonResponse({'success': False, 'message': message}, status=404)

    except json.JSONDecodeError:
        message = app_messages.error('RequisiÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o invÃƒÆ’Ã‚Â¡lida. JSON malformado.')
        return JsonResponse({'success': False, 'message': message}, status=400)
    except Exception as e:
        traceback.print_exc()
        message = app_messages.error(f'Erro ao excluir notas fiscais: {str(e)}')
        return JsonResponse({'success': False, 'message': message}, status=500)


@login_required_json
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
# ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸Ãƒâ€¦Ã‚Â¡ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ VIEW PARA CRIAR NOTA FISCAL DE SAIDA
# ==============================================================================
@login_required_json
# @permission_required('nota_fiscal.add_notafiscal', raise_exception=True) # Adicionar permissÃƒÆ’Ã‚Â£o depois
def criar_nfe_saida(request):
    """
    Renderiza o formulÃƒÆ’Ã‚Â¡rio para criar uma nova Nota Fiscal de SaÃƒÆ’Ã‚Â­da e processa a sua submissÃƒÆ’Ã‚Â£o.
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
            # Gerar nÃƒÆ’Ã‚Âºmero e chave de acesso provisÃƒÆ’Ã‚Â³rios
            nova_nota.numero = str(NotaFiscal.objects.count() + 1).zfill(9)
            nova_nota.chave_acesso = f"TEMP-{timezone.now().strftime('%Y%m%d%H%M%S')}-{nova_nota.numero}"
            nova_nota.save()
            
            messages.success(request, f"Nota Fiscal de SaÃƒÆ’Ã‚Â­da NÃƒâ€šÃ‚Âº {nova_nota.numero} criada com sucesso. Adicione os itens.")
            # Redireciona para a tela de ediÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o para adicionar itens
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

