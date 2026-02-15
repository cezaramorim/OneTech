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
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.text import slugify
# Removido o @csrf_exempt por razões de segurança
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from common.utils import render_ajax_or_base
from common.utils.formatters import converter_valor_br, converter_data_para_date, CustomDecimalEncoder
from fiscal.calculos import aplicar_impostos_na_nota
from empresas.models import EmpresaAvancada
from produto.models import CategoriaProduto, Produto, UnidadeMedida, DetalhesFiscaisProduto, NCM
from fiscal.models import CST, CSOSN
from .models import NotaFiscal, TransporteNotaFiscal, DuplicataNotaFiscal, ItemNotaFiscal
from produto.models_entradas import EntradaProduto
from .forms import (
    NotaFiscalForm,
    ItemNotaFiscalFormSet,
    DuplicataNotaFiscalFormSet,
    TransporteNotaFiscalFormSet,
    NotaFiscalSaidaForm
)

# --- Funções Auxiliares de Parsing --- #

def strip_namespace(tag):
    """Remove o namespace (ex: {http://...}) de uma tag XML."""
    return tag.split('}')[-1]

def xml_to_dict(element):
    """Converte um elemento XML e seus filhos em um dicionário, tratando namespaces."""
    result = {strip_namespace(element.tag): {}}
    
    # Adiciona atributos do elemento
    if element.attrib:
        result[strip_namespace(element.tag)].update(element.attrib)

    # Adiciona filhos
    for child in element:
        child_dict = xml_to_dict(child)
        child_tag = strip_namespace(child.tag)

        # Se a tag já existe, transforma em lista para agrupar múltiplos elementos
        if child_tag in result[strip_namespace(element.tag)]:
            if not isinstance(result[strip_namespace(element.tag)][child_tag], list):
                result[strip_namespace(element.tag)][child_tag] = [result[strip_namespace(element.tag)][child_tag]]
            result[strip_namespace(element.tag)][child_tag].append(child_dict[child_tag])
        else:
            result[strip_namespace(element.tag)].update(child_dict)

    # Adiciona o texto do elemento, se houver
    if element.text and element.text.strip():
        text = element.text.strip()
        # Se já houver filhos, adiciona o texto como uma chave especial
        if len(result[strip_namespace(element.tag)]) > 0:
            result[strip_namespace(element.tag)]['#text'] = text
        # Senão, o valor da tag é apenas o texto
        else:
            result[strip_namespace(element.tag)] = text
            
    return result

# --- Views Principais --- #

@login_required_json
@require_GET
def emitir_nfe_list_view(request):
    """
    Lista as notas fiscais que estão prontas para serem emitidas (status em branco ou 'rascunho').
    """
    # Filtra notas do emitente que é o tenant atual e que ainda não foram enviadas.
    # O status pode ser '' (vazio) ou um status específico como 'rascunho'.
    emitente = getattr(request.tenant, "emitente_padrao", None)
    notas_para_emitir = NotaFiscal.objects.filter(
        emitente_proprio=emitente,
        status_sefaz__in=['', None, 'rascunho']
    ).select_related('destinatario').order_by('-data_emissao')

    context = {
        'notas_para_emitir': notas_para_emitir,
        'content_template': 'partials/nota_fiscal/emitir_nfe_list.html',
        'data_page': 'emitir_nfe_list',
    }
    
    return render_ajax_or_base(request, context['content_template'], context)


@login_required_json
@require_GET
def importar_xml_view(request):
    """Renderiza a página de upload de XML para importação de notas fiscais."""
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
    exibir o preview da nota e gerenciar a revisão de itens, incluindo aviso de duplicidade.
    """
    app_messages = get_app_messages(request)
    print("--- Iniciando importação e parsing de XML ---")    
    print(f"DEBUG: Conteúdo de request.FILES: {request.FILES}")
    
    xml_file = request.FILES.get('xml')
    
    if xml_file:
        print(f"DEBUG: xml_file encontrado. Tipo: {type(xml_file)}")
        print(f"DEBUG: Nome do arquivo original: '{xml_file.name}'")
        print(f"DEBUG: Nome do arquivo em minúsculas e sem espaços: '{xml_file.name.lower().strip()}'")
        is_xml_file = xml_file.name.lower().strip().endswith('.xml')
        print(f"DEBUG: Resultado de .endswith('.xml'): {is_xml_file}")
    else:
        print("DEBUG: Nenhum arquivo XML encontrado em request.FILES.get('xml').")
        
    # 1. Verificação de Permissão do Usuário
    if not request.user.has_perm('nota_fiscal.can_import_xml'):
        message = app_messages.error('Você não tem permissão para importar XML de Notas Fiscais.')
        return JsonResponse({'success': False, 'message': message}, status=403)

    if not xml_file or not xml_file.name.lower().strip().endswith('.xml'):
        print(f"DEBUG: Condição de arquivo XML inválido acionada. xml_file is None: {xml_file is None}")
        if xml_file:
            print(f"DEBUG: xml_file.name.lower().strip().endswith('.xml'): {xml_file.name.lower().strip().endswith('.xml')}")
        message = app_messages.error('Arquivo XML inválido ou não fornecido.')
        return JsonResponse({'success': False, 'message': message}, status=400)

    try:
        # 2. Parsing do XML
        print("DEBUG: Tentando parsear o arquivo XML...")
        tree = ET.parse(xml_file)
        root = tree.getroot()
        print(f"DEBUG: XML parseado com sucesso. Root tag: {root.tag}")
        
        # Usa a função xml_to_dict (element_to_dict de utils.py) para parsear o XML completo
        full_xml_dict = xml_to_dict(root).get('nfeProc', {})
        print(f"DEBUG: Conteúdo de full_xml_dict (primeiros 200 chars): {str(full_xml_dict)[:200]}...")

        infNFe = full_xml_dict.get('NFe', {}).get('infNFe', {})
        if not infNFe:
            print("ERRO: Estrutura do XML inválida: <infNFe> não encontrado.")
            message = app_messages.error('Estrutura do XML inválida: <infNFe> não encontrado.')
            return JsonResponse({'success': False, 'message': message}, status=400)
        print("DEBUG: <infNFe> encontrado no XML.")

        # 3. Extração da Chave de Acesso e Verificação de Duplicidade
        chave = infNFe.get('Id', '').replace('NFe', '')
        
        if not chave:
            print("ERRO: Não foi possível extrair a chave de acesso do XML.")
            message = app_messages.error('Não foi possível extrair a chave de acesso do XML.')
            return JsonResponse({'success': False, 'message': message}, status=400)
        print(f"DEBUG: Chave de acesso extraída: {chave}")

        is_duplicate = False
        if NotaFiscal.objects.filter(chave_acesso=chave).exists():
            is_duplicate = True
            print(f"--- Nota Fiscal com a chave de acesso {chave} já existe no sistema. (Detectado como duplicata) ---")

        # Extração de dados principais para o preview
        ide = infNFe.get('ide', {})
        emit = infNFe.get('emit', {}) # Obter dados do emitente
        total = infNFe.get('total', {}).get('ICMSTot', {})
        print(f"DEBUG: Dados IDE: {ide.get('nNF', 'N/A')}, Total NF: {total.get('vNF', 'N/A')}")

        # Extrair a razão social do emitente
        nome_razao_social_emitente = emit.get('xNome', 'Nome do Emitente Não Encontrado')
        print(f"DEBUG: Nome/Razão Social do Emitente: {nome_razao_social_emitente}") # Adicionado para depuração
        
        # 4. Montagem da Lista de Produtos e Itens para Revisão
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
                'ncm': prod.get('NCM', ''),
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
        print(f"DEBUG: {len(itens_para_revisar)} produto(s) precisam de revisão.")
        
        # 5. Montagem da Resposta JSON para o Frontend
        message = 'XML processado com sucesso! Verifique os itens para revisão de categoria, se houver.'
        if is_duplicate:
            message = f'Esta Nota Fiscal (Chave: {chave}) já existe no sistema. Deseja importá-la novamente e atualizar os dados existentes?'

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
        
        print("--- Parsing de XML concluído com sucesso ---")
        response = JsonResponse(response_payload_for_frontend, encoder=CustomDecimalEncoder)
        print(f"DEBUG: Content-Type da resposta: {response['Content-Type']}")
        return response

    except Exception as e:
        print(f"ERRO CRÍTICO em importar_xml_nfe_view: {type(e).__name__} - {e}")
        full_traceback = traceback.format_exc()
        print(f"TRACEBACK COMPLETO:\n{full_traceback}") 
        message = app_messages.error(f'Ocorreu um erro no servidor ao processar o XML: {str(e)}')
        return JsonResponse({'success': False, 'message': message}, status=500)
@login_required_json
# @csrf_exempt REMOVIDO: `require_POST` já garante a proteção CSRF adequada para POST requests.
@require_POST
@transaction.atomic # Garante que todas as operações de banco de dados sejam atômicas
def processar_importacao_xml_view(request):
    app_messages = get_app_messages(request)
    """
    View unificada que recebe o JSON da nota (com categorias dos produtos já definidas),
    valida e salva a nota fiscal e todos os seus dados relacionados (empresas, produtos, itens, etc.)
    em uma única transação.
    """
    print("--- Iniciando processamento e salvamento da importação ---")
    try:
        payload = json.loads(request.body.decode('utf-8'))
        chave = payload.get('chave_acesso')
        force_update = payload.get('force_update', False)
        raw_payload = payload.get('raw_payload', {})

        if not chave or not raw_payload:
            return JsonResponse({'success': False, 'message': app_messages.error('Dados essenciais (chave de acesso ou payload) não encontrados.')}, status=400)

        infNFe = raw_payload.get('NFe', {}).get('infNFe', {})
        if not infNFe:
            return JsonResponse({'success': False, 'message': app_messages.error('Estrutura do XML inválida: <infNFe> não encontrado no raw_payload.')}, status=400)

        # Verifica se a nota fiscal já existe
        nota_existente = NotaFiscal.objects.filter(chave_acesso=chave).first()
        if nota_existente:
            if not force_update:
                message = app_messages.warning(f'A Nota Fiscal "{nota_existente.numero}" já foi importada. Deseja substituir os dados existentes?')
                return JsonResponse({
                    'success': True, 'message': message, 'nota_existente': True,
                    'nota_id': nota_existente.pk, 'redirect_url': reverse('nota_fiscal:entradas_nota')
                }, status=200)
            else:
                print(f"--- Excluindo nota fiscal existente (ID: {nota_existente.pk}) para atualização ---")
                nota_existente.delete()

        # 1. Processar Empresas (Emitente e Destinatário)
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

        # Mapeamento de código de produto para categoria para acesso rápido
        categorias_mapeadas = {str(p.get('codigo_produto')): p.get('categoria_id') for p in payload.get('itens_para_revisar', [])}

        # 3. PRÉ-PROCESSAMENTO AGREGADO PARA ATUALIZAÇÃO DE PRODUTOS
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
                    'dados_primeiro_item': prod_data, # Guarda dados para criação do produto
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
                item_nota_fiscal=ItemNotaFiscal.objects.latest('id'), # Pega o último item criado
                quantidade=Decimal(prod_data.get('qCom', '0')),
                preco_unitario=Decimal(prod_data.get('vUnCom', '0')),
                preco_total=Decimal(prod_data.get('vProd', '0')),
                fornecedor=emitente,
                nota_fiscal=nf,
                numero_nota=nf.numero,
            )
            # 4.4. Recalcula o estoque e preços do Produto mestre
            produto_obj.recalculate_stock_and_prices() # Chama o método para recalcular


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


# --- Funções de Apoio para `processar_importacao_xml_view` ---

def _get_or_create_empresa(data, tipo):
    """Cria ou obtém uma EmpresaAvancada a partir dos dados do XML (emitente ou destinatário)."""
    identificador = data.get('CNPJ') or data.get('CPF')
    if not identificador:
        raise ValueError(f"CNPJ/CPF não encontrado para {tipo}")

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

    empresa, created = EmpresaAvancada.objects.update_or_create(
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
    
    # Calcula o novo custo médio ponderado
    if produto.preco_custo and produto.estoque_atual > dados_agregados['quantidade_total']:
        valor_estoque_antigo = produto.preco_custo * (produto.estoque_atual - dados_agregados['quantidade_total'])
        novo_custo_medio = (valor_estoque_antigo + dados_agregados['valor_total_ponderado']) / produto.estoque_atual
        produto.preco_custo = novo_custo_medio
    else:
        # Se não há estoque anterior, o custo médio é o da nota
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
        ncm=prod_data.get('NCM'),
        cfop=prod_data.get('CFOP'),
        unidade=prod_data.get('uCom'),
        quantidade=Decimal(prod_data.get('qCom', '0')),
        valor_unitario=Decimal(prod_data.get('vUnCom', '0')),
        valor_total=Decimal(prod_data.get('vProd', '0')),
        desconto=Decimal(prod_data.get('vDesc', '0')),
        base_calculo_icms=Decimal(icms_data.get('vBC', '0')),
        aliquota_icms=Decimal(icms_data.get('pICMS', '0')),
        # Adicione outros campos de impostos conforme necessário
    )
    print(f"Item da nota criado: {item.descricao}")
    return item

def _create_transporte(nf, data):
    """Cria o registro de TransporteNotaFiscal."""
    vol = data.get('vol', {})
    if isinstance(vol, list): # Pega o primeiro volume se for uma lista
        vol = vol[0] if vol else {}

    TransporteNotaFiscal.objects.create(
        nota_fiscal=nf,
        modalidade_frete=data.get('modFrete', ''),
        transportadora_nome=(data.get('transporta') or {}).get('xNome', ''),
        transportadora_cnpj=(data.get('transporta') or {}).get('CNPJ', ''),
        quantidade_volumes=int(vol.get('qVol', 0) or 0),
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
    """Lista as notas fiscais de entrada com opção de busca e ordenação."""
    termo = request.GET.get('termo', '').strip()
    ordenacao = request.GET.get('ordenacao', '-data_emissao')

    # Usamos select_related para otimizar a busca, trazendo os dados do emitente e destinatário
    # em uma única consulta ao banco de dados.
    qs = NotaFiscal.objects.select_related('emitente', 'destinatario').all()

    if termo:
        qs = qs.filter(
            Q(numero__icontains=termo) |
            Q(emitente__razao_social__icontains=termo) |
            Q(emitente__nome__icontains=termo) |
            Q(destinatario__razao_social__icontains=termo) |
            Q(destinatario__nome__icontains=termo) |
            Q(chave_acesso__icontains=termo)
        )

    # Garante que a ordenação seja válida para evitar erros
    try:
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
    Renderiza a página para lançamento manual de notas fiscais,
    respondendo a requisições normais e AJAX.
    """
    categorias = list(CategoriaProduto.objects.order_by("nome").values("id", "nome"))
    empresas = list(EmpresaAvancada.objects.all().values(
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

    # Se a requisição for AJAX, retorna apenas o template parcial (o "miolo").
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, context['content_template'], context)

    # Para acesso direto via URL, retorna a página completa.
    return render(request, 'base.html', context)

# Substitua a sua função editar_nota_view por esta:

@login_required_json
@require_http_methods(["GET", "POST"] )
@transaction.atomic
def editar_nota_view(request, pk):
    """
    Lida com a criação (GET) e o processamento (POST) do formulário de edição de Nota Fiscal,
    respondendo a requisições normais e AJAX para a exibição do formulário.
    """
    app_messages = get_app_messages(request)
    nota = get_object_or_404(NotaFiscal, pk=pk)

    if request.method == 'POST':
        form = NotaFiscalForm(request.POST, instance=nota)
        item_formset = ItemNotaFiscalFormSet(request.POST, instance=nota, prefix='items')
        duplicata_formset = DuplicataNotaFiscalFormSet(request.POST, instance=nota, prefix='duplicatas')
        transporte_formset = TransporteNotaFiscalFormSet(request.POST, instance=nota, prefix='transporte')

        if form.is_valid() and item_formset.is_valid() and duplicata_formset.is_valid() and transporte_formset.is_valid():
            form.save()
            item_formset.save()
            duplicata_formset.save()
            transporte_formset.save()
            
            app_messages.success_updated(nota)
            return redirect('nota_fiscal:entradas_nota')
        else:
            app_messages.error("Foram encontrados erros no formulário. Por favor, corrija-os.")
            # A lógica de printar erros para debug pode ser mantida aqui...
            
    # A lógica para GET começa aqui
    form = NotaFiscalForm(instance=nota)
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

    # Se a requisição for AJAX (vinda de um clique em 'Editar' na lista),
    # renderiza apenas o template parcial.
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, context['content_template'], context)

    # Para acesso direto via URL ou em caso de erro no POST, renderiza a página completa.
    return render(request, 'base.html', context)

@login_required_json
@require_POST
@transaction.atomic
def excluir_notas_multiplo_view(request):
    app_messages = get_app_messages(request)
    """
    Exclui múltiplas notas fiscais com base nos IDs recebidos via POST.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        ids = data.get('ids', [])

        if not ids:
            message = app_messages.error('Nenhum ID fornecido para exclusão.')
            return JsonResponse({'success': False, 'message': message}, status=400)

        notas_excluidas, _ = NotaFiscal.objects.filter(id__in=ids).delete()

        if notas_excluidas > 0:
            message = app_messages.success_deleted("nota(s) fiscal(is)", f"{notas_excluidas} selecionada(s)")
            return JsonResponse({'success': True, 'message': message})
        else:
            message = app_messages.error('Nenhuma nota fiscal encontrada com os IDs fornecidos.')
            return JsonResponse({'success': False, 'message': message}, status=404)

    except json.JSONDecodeError:
        message = app_messages.error('Requisição inválida. JSON malformado.')
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
    produtos = Produto.objects.filter(
        Q(nome__icontains=termo) | Q(codigo_interno__icontains=termo) | Q(codigo_fornecedor__icontains=termo)
    ).select_related('unidade_medida_interna')[:50] # Limita a 50 resultados

    resultados = []
    for p in produtos:
        resultados.append({
            'id': p.id,
            'text': f"{p.codigo_interno} - {p.nome}",
            'codigo_interno': p.codigo_interno,
            'codigo_fornecedor': p.codigo_fornecedor,
            'nome': p.nome,
            'unidade': p.unidade_medida_interna.sigla if p.unidade_medida_interna else 'UN',
            'preco_venda': p.preco_venda,
            'ncm': p.detalhes_fiscais.ncm.codigo if hasattr(p, 'detalhes_fiscais') and p.detalhes_fiscais.ncm else '',
            'cfop': p.detalhes_fiscais.cfop if hasattr(p, 'detalhes_fiscais') else '',
        })

    return JsonResponse({'results': resultados})


# ==============================================================================
# 🚀 VIEW PARA CRIAR NOTA FISCAL DE SAÍDA
# ==============================================================================
@login_required_json
# @permission_required('nota_fiscal.add_notafiscal', raise_exception=True) # Adicionar permissão depois
def criar_nfe_saida(request):
    """
    Renderiza o formulário para criar uma nova Nota Fiscal de Saída e processa a sua submissão.
    """
    if request.method == 'POST':
        form = NotaFiscalSaidaForm(request.POST)
        if form.is_valid():
            # AINDA NÃO SALVA OS ITENS, apenas o cabeçalho da nota
            nova_nota = form.save(commit=False)
            nova_nota.created_by = request.user
            # Gerar número e chave de acesso provisórios
            nova_nota.numero = str(NotaFiscal.objects.count() + 1).zfill(9)
            nova_nota.chave_acesso = f"TEMP-{timezone.now().strftime('%Y%m%d%H%M%S')}-{nova_nota.numero}"
            nova_nota.save()
            
            messages.success(request, f"Nota Fiscal de Saída Nº {nova_nota.numero} criada com sucesso. Adicione os itens.")
            # Redireciona para a tela de edição para adicionar itens
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