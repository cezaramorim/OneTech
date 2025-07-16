# nota_fiscal/views.py

import os
import re
import json
import traceback
import datetime
import xml.etree.ElementTree as ET
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
# Removido o @csrf_exempt por razões de segurança
from django.views.decorators.http import require_GET, require_POST, require_http_methods

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
    TransporteNotaFiscalFormSet
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

@login_required
@require_GET
def importar_xml_view(request):
    """Renderiza a página de upload de XML para importação de notas fiscais."""
    categorias = list(CategoriaProduto.objects.order_by("nome").values("id", "nome"))
    context = {
        'categorias_disponiveis_json': json.dumps(categorias, ensure_ascii=False),
        'content_template': 'partials/nota_fiscal/importar_xml.html',
        'data_page': 'importar_xml',
    }
    return render(request, 'base.html', context)


@login_required
@require_POST
def importar_xml_nfe_view(request):
    """
    Recebe um arquivo XML, faz o parsing e retorna um JSON estruturado para o frontend
    exibir o preview da nota e gerenciar a revisão de itens, incluindo aviso de duplicidade.
    """
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
        return JsonResponse({'success': False, 'error': 'Você não tem permissão para importar XML de Notas Fiscais.'}, status=403)

    if not xml_file or not xml_file.name.lower().strip().endswith('.xml'):
        print(f"DEBUG: Condição de arquivo XML inválido acionada. xml_file is None: {xml_file is None}")
        if xml_file:
            print(f"DEBUG: xml_file.name.lower().strip().endswith('.xml'): {xml_file.name.lower().strip().endswith('.xml')}")
        return JsonResponse({'success': False, 'error': 'Arquivo XML inválido ou não fornecido.'}, status=400)

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
            return JsonResponse({'success': False, 'error': 'Estrutura do XML inválida: <infNFe> não encontrado.'}, status=400)
        print("DEBUG: <infNFe> encontrado no XML.")

        # 3. Extração da Chave de Acesso e Verificação de Duplicidade
        chave = infNFe.get('Id', '').replace('NFe', '') # Correção de '@Id' para 'Id' já aplicada
        
        if not chave:
            print("ERRO: Não foi possível extrair a chave de acesso do XML.")
            return JsonResponse({'success': False, 'error': 'Não foi possível extrair a chave de acesso do XML.'}, status=400)
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
        print(f"DEBUG: Encontrados {len(det_list)} item(s) na nota.")

        for det_item in det_list:
            prod = det_item.get('prod', {})
            codigo_importado = prod.get('cProd', '')

            produto_existente = Produto.objects.filter(codigo=codigo_importado).first()
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
        return JsonResponse(response_payload_for_frontend, encoder=CustomDecimalEncoder)

    except Exception as e:
        print(f"ERRO CRÍTICO em importar_xml_nfe_view: {type(e).__name__} - {e}")
        full_traceback = traceback.format_exc()
        print(f"TRACEBACK COMPLETO:\n{full_traceback}") 
        return JsonResponse({'success': False, 'error': f'Ocorreu um erro no servidor ao processar o XML: {str(e)}'}, status=500)
@login_required
# @csrf_exempt REMOVIDO: `require_POST` já garante a proteção CSRF adequada para POST requests.
@require_POST
@transaction.atomic # Garante que todas as operações de banco de dados sejam atômicas
def processar_importacao_xml_view(request):
    """
    View unificada que recebe o JSON da nota (com categorias dos produtos já definidas),
    valida e salva a nota fiscal e todos os seus dados relacionados (empresas, produtos, itens, etc.)
    em uma única transação.
    """
    print("--- Iniciando processamento e salvamento da importação ---")
    try:
        payload = json.loads(request.body.decode('utf-8'))
        chave = payload.get('chave_acesso')
        force_update = payload.get('force_update', False) # Novo parâmetro
        mensagem_sucesso = "Nota Fiscal importada e processada com sucesso!" # Inicializa a variável

        if not chave:
            return JsonResponse({'erro': 'Chave de acesso não encontrada no payload.'}, status=400)
        
        # Verifica se a nota fiscal já existe
        nota_existente = NotaFiscal.objects.filter(chave_acesso=chave).first()

        if nota_existente:
            if not force_update:
                # Se a nota existe e não é para forçar atualização, retorna alerta para o frontend
                return JsonResponse({
                    'mensagem': f'A Nota Fiscal "{nota_existente.numero}" Chave "{nota_existente.chave_acesso}" já foi importada, deseja substituir os dados já salvos?',
                    'nota_existente': True,
                    'nota_id': nota_existente.pk,
                    'redirect_url': reverse('nota_fiscal:entradas_nota')
                }, status=200) # Retorna 200 OK com flag para o frontend
            else:
                # Se force_update é True, exclui a nota existente e seus relacionados
                print(f"--- Excluindo nota fiscal existente (ID: {nota_existente.pk}) para atualização ---")
                nota_existente.delete() # CASCADE delete cuidará dos itens, transportes, duplicatas e entradas
                mensagem_sucesso = "Todos os dados da importação foram atualizados!"

        # 1. Processar e salvar Emitente e Destinatário
        emit_data = payload.get('emit', {})
        dest_data = payload.get('dest', {})
        
        emitente = _get_or_create_empresa(emit_data, 'emit')
        destinatario = _get_or_create_empresa(dest_data, 'dest')

        # 2. Criar a Nota Fiscal principal
        nf = NotaFiscal.objects.create(
            raw_payload=payload.get('raw_payload', {}),
            chave_acesso=chave,
            created_by=request.user,
            data_emissao=_parse_datetime(payload.get('data_emissao')),
            data_saida=_parse_datetime(payload.get('data_saida')),
            numero=payload.get('numero', ''),
            natureza_operacao=payload.get('natureza_operacao', ''),
            informacoes_adicionais=payload.get('informacoes_adicionais', ''),
            valor_total_nota=Decimal(payload.get('valor_total_nota', '0')),
            valor_total_produtos=Decimal(payload.get('valor_total_produtos', '0')),
            valor_total_icms=Decimal(payload.get('valor_total_icms', '0')),
            valor_total_pis=Decimal(payload.get('valor_total_pis', '0')),
            valor_total_cofins=Decimal(payload.get('valor_total_cofins', '0')),
            valor_total_desconto=Decimal(payload.get('valor_total_desconto', '0')),
            emitente=emitente,
            destinatario=destinatario,
        )
        print(f"DEBUG: Nota Fiscal {nf.numero} (ID: {nf.pk}) criada.")

        # Aplica os cálculos de impostos aos itens da nota fiscal
        aplicar_impostos_na_nota(nf)

        # 3. Processar Produtos e Itens da Nota
        # Agrupar produtos por código para somar quantidades e valores, e calcular média ponderada do valor unitário
        produtos_agrupados = {}
        for prod_data_raw in payload.get('produtos', []):
            codigo_item = prod_data_raw.get('codigo', '')
            
            quantidade_atual = Decimal(prod_data_raw.get('quantidade', '0'))
            valor_total_atual = Decimal(prod_data_raw.get('valor_total', '0'))
            desconto_atual = Decimal(prod_data_raw.get('desconto', '0'))
            valor_unitario_atual = Decimal(prod_data_raw.get('valor_unitario', '0'))

            if codigo_item not in produtos_agrupados:
                produtos_agrupados[codigo_item] = {
                    'first_prod_data': prod_data_raw, # Mantém os dados do primeiro item para campos gerais
                    'quantities_and_unit_values': [], # Lista de (quantidade, valor_unitario) para média ponderada
                    'quantidade_total': Decimal('0'),
                    'valor_total_item': Decimal('0'),
                    'desconto_total': Decimal('0'),
                }
            
            produtos_agrupados[codigo_item]['quantities_and_unit_values'].append({
                'quantidade': quantidade_atual,
                'valor_unitario': valor_unitario_atual
            })
            produtos_agrupados[codigo_item]['quantidade_total'] += quantidade_atual
            produtos_agrupados[codigo_item]['valor_total_item'] += valor_total_atual
            produtos_agrupados[codigo_item]['desconto_total'] += desconto_atual

        for codigo_item, aggregated_data in produtos_agrupados.items():
            # Calcula a média ponderada para o valor_unitario
            total_valor_x_quantidade = Decimal('0')
            total_quantidade_para_media = Decimal('0')

            for item_entry in aggregated_data['quantities_and_unit_values']:
                total_valor_x_quantidade += item_entry['valor_unitario'] * item_entry['quantidade']
                total_quantidade_para_media += item_entry['quantidade']
            
            if total_quantidade_para_media > 0:
                aggregated_valor_unitario = total_valor_x_quantidade / total_quantidade_para_media
            else:
                # Se a quantidade total for zero, usa o valor unitário do primeiro item (ou zero)
                aggregated_valor_unitario = Decimal(aggregated_data['first_prod_data'].get('vUnCom', '0')) # Use vUnCom do XML

            prod_data_for_item_creation = aggregated_data['first_prod_data']
            
            # Extrair detalhes de impostos ANTES de criar/atualizar o produto e detalhes fiscais
            imposto_detalhes = prod_data_for_item_creation.get('imposto_detalhes', {})
            
            produto = _get_or_create_produto(prod_data_for_item_creation, emitente)

            # Cria ou atualiza os DetalhesFiscaisProduto
            _get_or_create_detalhes_fiscais_produto(produto, imposto_detalhes, prod_data_for_item_creation)

            # --- Lógica de Conversão de Unidade e Quantidade ---
            quantidade_xml = aggregated_data['quantidade_total']
            valor_unitario_xml = aggregated_valor_unitario

            # Garante que o objeto produto tenha os dados mais recentes do banco de dados
            produto.refresh_from_db()

            # A conversão agora usa o fator do próprio produto
            fator_conversao = produto.fator_conversao if produto.fator_conversao > 0 else 1
            
            print(f"DEBUG: Fator de conversão lido do produto: {produto.fator_conversao}")
            print(f"DEBUG: Fator de conversão usado no cálculo: {fator_conversao}")
            print(f"DEBUG: Valores antes da conversão - quantidade_xml: {quantidade_xml}, valor_unitario_xml: {valor_unitario_xml}, fator_conversao: {fator_conversao}")

            quantidade_para_estoque = quantidade_xml * fator_conversao
            # Evita divisão por zero se o fator for 0
            preco_para_estoque = valor_unitario_xml / fator_conversao if fator_conversao > 0 else valor_unitario_xml

            if fator_conversao != 1:
                print(f"DEBUG: Conversão aplicada para {produto.nome}: {quantidade_xml} (unidade compra) -> {quantidade_para_estoque} ({produto.unidade_medida_interna})")
                print(f"DEBUG: Preço convertido para {produto.nome}: {valor_unitario_xml} (preço compra) -> {preco_para_estoque} (preço interno)")
            # --- Fim da Lógica de Conversão ---
            
            # ICMS
            icms_data = {}
            for key, value in imposto_detalhes.get('ICMS', {}).items():
                if isinstance(value, dict): # Pode ser ICMS00, ICMS40, etc.
                    icms_data = value
                    break
            
            # IPI
            ipi_data = imposto_detalhes.get('IPI', {}).get('IPITrib', {}) or imposto_detalhes.get('IPI', {}).get('IPINT', {})

            # PIS
            pis_data = imposto_detalhes.get('PIS', {}).get('PISAliq', {}) or imposto_detalhes.get('PIS', {}).get('PISQtde', {}) or imposto_detalhes.get('PIS', {}).get('PISNT', {}) or imposto_detalhes.get('PIS', {}).get('PISOutr', {})

            # COFINS
            cofins_data = imposto_detalhes.get('COFINS', {}).get('COFINSAliq', {}) or imposto_detalhes.get('COFINS', {}).get('COFINSQtde', {}) or imposto_detalhes.get('COFINS', {}).get('COFINSNT', {}) or imposto_detalhes.get('COFINS', {}).get('COFINSOutr', {})

            # Get CST/CSOSN objects for ItemNotaFiscal
            cst_icms_aplicado_obj = None
            csosn_icms_aplicado_obj = None
            cst_ipi_aplicado_obj = None
            cst_pis_aplicado_obj = None
            cst_cofins_aplicado_obj = None # Inicializa a variável aqui

            cst_icms_code_aplicado = icms_data.get('CST', '')
            csosn_icms_code_aplicado = icms_data.get('CSOSN', '')

            if cst_icms_code_aplicado:
                cst_icms_aplicado_obj, _ = CST.objects.get_or_create(
                    codigo=cst_icms_code_aplicado,
                    defaults={'descricao': f'CST {cst_icms_code_aplicado}'}
                )
            elif csosn_icms_code_aplicado:
                csosn_icms_aplicado_obj, _ = CSOSN.objects.get_or_create(
                    codigo=csosn_icms_code_aplicado,
                    defaults={'descricao': f'CSOSN {csosn_icms_code_aplicado}'}
                )

            ipi_cst_code_aplicado = ipi_data.get('CST', '')
            if ipi_cst_code_aplicado:
                cst_ipi_aplicado_obj, _ = CST.objects.get_or_create(
                    codigo=ipi_cst_code_aplicado,
                    defaults={'descricao': f'CST {ipi_cst_code_aplicado}'}
                )

            pis_cst_code_aplicado = pis_data.get('CST', '')
            if pis_cst_code_aplicado:
                cst_pis_aplicado_obj, _ = CST.objects.get_or_create(
                    codigo=pis_cst_code_aplicado,
                    defaults={'descricao': f'CST {pis_cst_code_aplicado}'}
                )

            cofins_cst_code_aplicado = cofins_data.get('CST', '')
            if cofins_cst_code_aplicado:
                cst_cofins_aplicado_obj, _ = CST.objects.get_or_create(
                    codigo=cofins_cst_code_aplicado,
                    defaults={'descricao': f'CST {cofins_cst_code_aplicado}'}
                )

            item_nota, created = ItemNotaFiscal.objects.update_or_create(
                nota_fiscal=nf,
                codigo=codigo_item,
                defaults={
                    'produto': produto,
                    'descricao': produto.nome, # Usa o nome do produto do banco de dados
                    'unidade': prod_data_for_item_creation.get('uCom', ''),
                    'quantidade': quantidade_xml, # Usa a quantidade ORIGINAL do XML
                    'valor_unitario': valor_unitario_xml, # Usa o valor unitário ORIGINAL
                    'valor_total': aggregated_data['valor_total_item'],
                    'desconto': aggregated_data['desconto_total'],

                    # Campos de impostos detalhados por item
                    'base_calculo_icms': Decimal(icms_data.get('vBC', '0')),
                    'aliquota_icms': Decimal(icms_data.get('pICMS', '0')),
                    'valor_icms_desonerado': Decimal(icms_data.get('vICMSDeson', '0')),
                    'motivo_desoneracao_icms': icms_data.get('motDesICMS', ''),
                    'cst_icms_cst_aplicado': cst_icms_aplicado_obj,
                    'cst_icms_csosn_aplicado': csosn_icms_aplicado_obj,

                    'base_calculo_ipi': Decimal(ipi_data.get('vBC', '0')),
                    'aliquota_ipi': Decimal(ipi_data.get('pIPI', '0')),
                    'cst_ipi_aplicado': cst_ipi_aplicado_obj,

                    'base_calculo_pis': Decimal(pis_data.get('vBC', '0')),
                    'aliquota_pis': Decimal(pis_data.get('pPIS', '0')),
                    'cst_pis_aplicado': cst_pis_aplicado_obj,

                    'base_calculo_cofins': Decimal(cofins_data.get('vBC', '0')),
                    'aliquota_cofins': Decimal(cofins_data.get('pCOFINS', '0')),
                    'cst_cofins_aplicado': cst_cofins_aplicado_obj,
                }
            )
            print(f"DEBUG: ItemNotaFiscal {'criado' if created else 'atualizado'}: {item_nota.codigo} (ID: {item_nota.pk})")
            
            # 4. Criar ou atualizar a Entrada de Produto no estoque com valores CONVERTIDOS
            entrada_produto, created_entrada = EntradaProduto.objects.update_or_create(
                item_nota_fiscal=item_nota,
                defaults={
                    'quantidade': quantidade_para_estoque, # Usa a quantidade CONVERTIDA
                    'preco_unitario': preco_para_estoque, # Usa o preço CONVERTIDO
                    'preco_total': aggregated_data['valor_total_item'], # O valor total do item permanece o mesmo
                    'fornecedor': emitente, # Adiciona o fornecedor à EntradaProduto
                    'nota_fiscal': nf, # Adiciona a nota fiscal à EntradaProduto
                    'numero_nota': nf.numero, # Adiciona o número da nota à EntradaProduto
                }
            )
            print(f"DEBUG: EntradaProduto {'criada' if created_entrada else 'atualizada'}: {entrada_produto.quantidade} {entrada_produto.item_nota_fiscal.produto.unidade_medida_interna} de {entrada_produto.item_nota_fiscal.produto.nome}")

        # 5. Processar Transporte (se houver)
        transp_data = payload.get('transporte', {})
        if transp_data:
            _create_transporte(nf, transp_data)

        # 6. Processar Duplicatas (se houver)
        cobr_data = payload.get('cobranca', {})
        if cobr_data and 'dup' in cobr_data:
            _create_duplicatas(nf, cobr_data.get('dup', []))

        print(f"--- Sucesso: Nota Fiscal {nf.numero} (ID: {nf.pk}) salva com sucesso. ---")
        return JsonResponse({
            'success': True,
            'mensagem': mensagem_sucesso,
            'nota_id': nf.pk,
            'redirect_url': reverse('nota_fiscal:entradas_nota')
        }, status=201)

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'erro': f'Ocorreu um erro inesperado no servidor: {str(e)}'}, status=500)


# --- Funções de Apoio para `processar_importacao_xml_view` ---

def _get_or_create_empresa(data, tipo):
    """Cria ou obtém uma EmpresaAvancada a partir dos dados do XML (emitente ou destinatário)."""
    identificador = data.get('CNPJ') or data.get('CPF')
    if not identificador:
        raise ValueError(f"CNPJ/CPF não encontrado para {tipo}")

    identificador_limpo = re.sub(r'\D', '', identificador)
    is_cnpj = len(identificador_limpo) == 14

    lookup_field = 'cnpj' if is_cnpj else 'cpf'
    lookup_value = identificador_limpo
    
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
        **{lookup_field: lookup_value},
        defaults=defaults
    )
    print(f"Empresa ({tipo}) {'criada' if created else 'encontrada'}: {empresa}")
    return empresa

def _get_or_create_produto(data, fornecedor):
    """Cria ou atualiza um Produto a partir dos dados do XML, preservando campos existentes como categoria."""
    print(f"--- Debug: _get_or_create_produto para dados: {data} ---")
    
    # O payload do item ('det') contém um dicionário 'prod' com os detalhes do produto.
    prod_data = data.get('prod', {})

    codigo_produto = prod_data.get('cProd')
    if not codigo_produto:
        # Lança um erro claro se o código do produto estiver ausente,
        # em vez de deixar o banco de dados falhar com um erro de integridade.
        raise ValueError("O código do produto ('cProd') está ausente nos dados do item.")

    categoria_id = prod_data.get('categoria_id')  # Adicionado pelo frontend
    categoria = get_object_or_404(CategoriaProduto, pk=categoria_id) if categoria_id else None

    unidade_xml_sigla = prod_data.get('uCom', '')
    unidade_fornecedor_obj, _ = UnidadeMedida.objects.get_or_create(
        sigla=unidade_xml_sigla,
        defaults={'descricao': f'Unidade {unidade_xml_sigla}'}
    )

    produto = Produto.objects.filter(codigo=codigo_produto).first()

    if produto:  # Produto já existe
        produto.refresh_from_db()
        produto.nome = prod_data.get('xProd', produto.nome)
        produto.preco_custo = Decimal(prod_data.get('vUnCom', produto.preco_custo))
        produto.preco_venda = Decimal(prod_data.get('vUnCom', produto.preco_venda))
        produto.preco_medio = Decimal(prod_data.get('vUnCom', produto.preco_medio))
        produto.fornecedor = fornecedor
        produto.unidade_fornecedor_padrao = unidade_fornecedor_obj
        produto.controla_estoque = True
        
        if produto.categoria is None and categoria is not None:
            produto.categoria = categoria

        produto.save(update_fields=[
            'nome', 'preco_custo', 'preco_venda', 'preco_medio', 'fornecedor',
            'unidade_fornecedor_padrao', 'categoria', 'controla_estoque'
        ])
        print(f"DEBUG: Produto existente atualizado: {produto.nome}")
    else:  # Produto é novo
        produto = Produto.objects.create(
            codigo=codigo_produto,
            nome=prod_data.get('xProd', ''),
            preco_custo=Decimal(prod_data.get('vUnCom', '0')),
            preco_venda=Decimal(prod_data.get('vUnCom', '0')),
            preco_medio=Decimal(prod_data.get('vUnCom', '0')),
            fornecedor=fornecedor,
            unidade_medida_interna=None,
            fator_conversao=Decimal('1'),
            unidade_fornecedor_padrao=unidade_fornecedor_obj,
            controla_estoque=True,
            ativo=True,
            categoria=categoria,
        )
        print(f"DEBUG: Novo produto criado: {produto.nome}")

    return produto

def _get_or_create_detalhes_fiscais_produto(produto, imposto_detalhes, prod_data_for_item_creation):
    """Cria ou atualiza os DetalhesFiscaisProduto para um produto."""

    # Extrair dados fiscais
    icms_data = {}
    for key, value in imposto_detalhes.get('ICMS', {}).items():
        if isinstance(value, dict): # Pode ser ICMS00, ICMS40, etc.
            icms_data = value
            break
    
    ipi_data = imposto_detalhes.get('IPI', {}).get('IPITrib', {}) or imposto_detalhes.get('IPI', {}).get('IPINT', {})
    pis_data = imposto_detalhes.get('PIS', {}).get('PISAliq', {}) or imposto_detalhes.get('PIS', {}).get('PISQtde', {}) or imposto_detalhes.get('PIS', {}).get('PISNT', {}) or imposto_detalhes.get('PIS', {}).get('PISOutr', {})
    cofins_data = imposto_detalhes.get('COFINS', {}).get('COFINSAliq', {}) or imposto_detalhes.get('COFINS', {}).get('COFINSQtde', {}) or imposto_detalhes.get('COFINS', {}).get('COFINSNT', {}) or imposto_detalhes.get('COFINS', {}).get('COFINSOutr', {})

    # Tenta obter o NCM existente ou cria um novo
    ncm_codigo = prod_data_for_item_creation.get('ncm', '')
    ncm_obj = None
    if ncm_codigo:
        ncm_obj, created_ncm = NCM.objects.get_or_create(
            codigo=ncm_codigo,
            defaults={'descricao': f'NCM {ncm_codigo}'}
        )

    # Inicializa todos os objetos CST/CSOSN como None
    cst_icms_obj = None
    csosn_icms_obj = None
    cst_ipi_obj = None
    cst_pis_obj = None
    cst_cofins_obj = None # Inicializa a variável aqui

    # Get CST/CSOSN objects
    cst_icms_code = icms_data.get('CST', '')
    csosn_icms_code = icms_data.get('CSOSN', '')

    if cst_icms_code:
        cst_icms_obj, _ = CST.objects.get_or_create(
            codigo=cst_icms_code,
            defaults={'descricao': f'CST {cst_icms_code}'}
        )
    elif csosn_icms_code:
        csosn_icms_obj, _ = CSOSN.objects.get_or_create(
            codigo=csosn_icms_code,
            defaults={'descricao': f'CSOSN {csosn_icms_code}'}
        )

    ipi_cst_code = ipi_data.get('CST', '')
    if ipi_cst_code:
        cst_ipi_obj, _ = CST.objects.get_or_create(
            codigo=ipi_cst_code,
            defaults={'descricao': f'CST {ipi_cst_code}'}
        )

    pis_cst_code = pis_data.get('CST', '')
    if pis_cst_code:
        cst_pis_obj, _ = CST.objects.get_or_create(
            codigo=pis_cst_code,
            defaults={'descricao': f'CST {pis_cst_code}'}
        )

    cofins_cst_code = cofins_data.get('CST', '')
    if cofins_cst_code:
        cst_cofins_obj, _ = CST.objects.get_or_create(
            codigo=cofins_cst_code,
            defaults={'descricao': f'CST {cofins_cst_code}'}
        )

    defaults = {
        'cst_icms_cst': cst_icms_obj, # Assign to CST FK
        'cst_icms_csosn': csosn_icms_obj, # Assign to CSOSN FK
        'origem_mercadoria': icms_data.get('orig', ''),
        'aliquota_icms_interna': Decimal(icms_data.get('pICMS', '0')),
        'reducao_base_icms': Decimal(icms_data.get('pRedBC', '0')),
        'cst_ipi': cst_ipi_obj,
        'cst_pis': cst_pis_obj,
        'cst_cofins': cst_cofins_obj, # Usando a variável corretamente inicializada
        'cest': prod_data_for_item_creation.get('cest', ''), # CEST do XML
        'ncm': ncm_obj, # NCM do XML
        'cfop': prod_data_for_item_creation.get('cfop', ''), # CFOP do XML
        'unidade_comercial': prod_data_for_item_creation.get('unidade', ''),
        'quantidade_comercial': Decimal(prod_data_for_item_creation.get('quantidade', '0')),
        'valor_unitario_comercial': Decimal(prod_data_for_item_creation.get('valor_unitario', '0')),
        'codigo_produto_fornecedor': prod_data_for_item_creation.get('codigo', ''),
    }

    print(f"DEBUG: Defaults para DetalhesFiscaisProduto: {defaults}")
    detalhes_fiscais, created = DetalhesFiscaisProduto.objects.update_or_create(
        produto=produto,
        defaults=defaults
    )
    print(f"DEBUG: DetalhesFiscaisProduto {'criado' if created else 'atualizado'}: {detalhes_fiscais.pk}")
    return detalhes_fiscais

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

@login_required
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


@login_required
@require_GET
def lancar_nota_manual_view(request):
    """
    Renderiza a página para lançamento manual de notas fiscais.
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
    }
    return render(request, 'base.html', context)

@login_required
@require_http_methods(["GET", "POST"])
@transaction.atomic
def editar_nota_view(request, pk):
    """Lida com a edição de uma Nota Fiscal e seus dados relacionados."""
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
            
            messages.success(request, f"Nota Fiscal {nota.numero} atualizada com sucesso!")
            return redirect('nota_fiscal:entradas_nota')
        else:
            # Se houver erros, exibe-os para o usuário
            messages.error(request, "Foram encontrados erros no formulário. Por favor, corrija-os.")
            print("\n--- Erros de Validação ---")
            if form.errors:
                print(f"Formulário principal: {form.errors}")
            if item_formset.errors:
                print(f"Formset de Itens: {item_formset.errors}")
            if item_formset.non_form_errors():
                print(f"Formset de Itens (erros não de campo): {item_formset.non_form_errors()}")
            if duplicata_formset.errors:
                print(f"Formset de Duplicatas: {duplicata_formset.errors}")
            if duplicata_formset.non_form_errors():
                print(f"Formset de Duplicatas (erros não de campo): {duplicata_formset.non_form_errors()}")
            if transporte_formset.errors:
                print(f"Formset de Transporte: {transporte_formset.errors}")
            if transporte_formset.non_form_errors():
                print(f"Formset de Transporte (erros não de campo): {transporte_formset.non_form_errors()}")
            print("--------------------------")

    else: # GET
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
    }
    return render(request, 'base.html', context)

@login_required
@require_POST
@transaction.atomic
def excluir_notas_multiplo_view(request):
    """
    Exclui múltiplas notas fiscais com base nos IDs recebidos via POST.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        ids = data.get('ids', [])

        if not ids:
            return JsonResponse({'sucesso': False, 'mensagem': 'Nenhum ID fornecido para exclusão.'}, status=400)

        # Filtra as notas fiscais que pertencem ao usuário logado (opcional, mas boa prática de segurança)
        # ou que o usuário tem permissão para excluir.
        # Por enquanto, vamos apenas excluir as notas com os IDs fornecidos.
        notas_excluidas, _ = NotaFiscal.objects.filter(id__in=ids).delete()

        if notas_excluidas > 0:
            return JsonResponse({'sucesso': True, 'mensagem': f'{notas_excluidas} nota(s) fiscal(is) excluída(s) com sucesso.'})
        else:
            return JsonResponse({'sucesso': False, 'mensagem': 'Nenhuma nota fiscal encontrada com os IDs fornecidos.'}, status=404)

    except json.JSONDecodeError:
        return JsonResponse({'sucesso': False, 'mensagem': 'Requisição inválida. JSON malformado.'}, status=400)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao excluir notas fiscais: {str(e)}'}, status=500)
