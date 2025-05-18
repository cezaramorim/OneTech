# nota_fiscal/views.py

import os
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
import xml.etree.ElementTree as ET
from django.conf import settings
from django.contrib import messages # Adicionado para mensagens
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect # Adicionado redirect
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from django.db.models import Q
# 📦 Models
from produto.models import NCM
from produto.models_entradas import EntradaProduto
from empresas.models import EmpresaAvancada
from nota_fiscal.models import NotaFiscal, TransporteNotaFiscal, DuplicataNotaFiscal, ItemNotaFiscal
from produto.models import Produto
from produto.models import UnidadeMedida

# 📝 Formulários
from .forms import NotaFiscalForm

# 🔄 Serializers & Filtros (agora centralizados em `common`)
from common.serializers.nota_fiscal import NotaFiscalSerializer
from common.filters.nota_fiscal import NotaFiscalFilter

# 🛠️ Utilitários de formatação
from common.utils.formatters import (
    formatar_moeda_br,
    formatar_data_iso_para_br,
    converter_valor_br,
    converter_data_para_date,
    formatar_dados_para_br
)


@login_required
def importar_xml_view(request):
    """Renderiza a página de upload de XML com suporte a AJAX e carregamento completo."""
    partial_template = "partials/nota_fiscal/importar_xml.html"
    base_template = "base.html"
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, partial_template)
    
    context = {
        "content_template": partial_template,
        "data_page": "importar-xml"
    }
    return render(request, base_template, context)


@login_required
@csrf_exempt
@require_POST
def importar_xml_nfe_view(request):
    """
    Processa upload de XML da NFe e retorna JSON com TODOS os campos
    (nota, fornecedor, produtos, totais, transporte, duplicatas, info_adicional, chave_acesso),
    mantendo as datas em ISO (YYYY-MM-DD).
    """
    xml_file = request.FILES.get("xml")
    if not xml_file or not xml_file.name.lower().endswith(".xml"):
        return JsonResponse({"erro": "Arquivo XML inválido."}, status=400)
    
    caminho = None # Inicializa a variável caminho
    try:
        nome_seguro = slugify(xml_file.name)
        # Garante que o diretório xmls_temp exista dentro de MEDIA_ROOT
        dir_xmls_temp = os.path.join(settings.MEDIA_ROOT, "xmls_temp")
        os.makedirs(dir_xmls_temp, exist_ok=True)
        caminho = os.path.join(dir_xmls_temp, nome_seguro)
        
        with default_storage.open(caminho, "wb+") as destino:
            for chunk in xml_file.chunks():
                destino.write(chunk)

        tree = ET.parse(caminho)
        root = tree.getroot()
        ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}

        raw_dhEmi    = root.findtext(".//nfe:ide/nfe:dhEmi", namespaces=ns) or ""
        raw_dEmi     = root.findtext(".//nfe:ide/nfe:dEmi",  namespaces=ns) or ""
        raw_dhSaiEnt = root.findtext(".//nfe:ide/nfe:dhSaiEnt", namespaces=ns) or ""
        raw_dSaiEnt  = root.findtext(".//nfe:ide/nfe:dSaiEnt",  namespaces=ns) or ""
        data_emissao = (raw_dhEmi or raw_dEmi).split("T")[0] if (raw_dhEmi or raw_dEmi) else ""
        data_saida   = (raw_dhSaiEnt or raw_dSaiEnt).split("T")[0] if (raw_dhSaiEnt or raw_dSaiEnt) else ""

        nota = {
            "numero_nota":       root.findtext(".//nfe:ide/nfe:nNF", namespaces=ns) or "",
            "data_emissao":      data_emissao,
            "data_saida":        data_saida,
            "natureza_operacao": root.findtext(".//nfe:ide/nfe:natOp", namespaces=ns) or ""
        }

        emit = root.find(".//nfe:emit", namespaces=ns)
        fornecedor = {}
        if emit is not None:
            end = emit.find("nfe:enderEmit", namespaces=ns)
            fornecedor = {
                "cnpj":          emit.findtext("nfe:CNPJ", namespaces=ns) or "",
                "razao_social":  emit.findtext("nfe:xNome", namespaces=ns) or "",
                "nome_fantasia": emit.findtext("nfe:xFant", namespaces=ns) or "",
                "logradouro":    end.findtext("nfe:xLgr", namespaces=ns)   if end is not None else "",
                "numero":        end.findtext("nfe:nro", namespaces=ns)    if end is not None else "",
                "bairro":        end.findtext("nfe:xBairro", namespaces=ns)if end is not None else "",
                "municipio":     end.findtext("nfe:xMun", namespaces=ns)   if end is not None else "",
                "uf":            end.findtext("nfe:UF", namespaces=ns)     if end is not None else "",
                "cep":           end.findtext("nfe:CEP", namespaces=ns)    if end is not None else "",
                "telefone":      end.findtext("nfe:fone", namespaces=ns)   if end is not None else ""
            }

        produtos = []
        for det in root.findall(".//nfe:det", namespaces=ns):
            prod    = det.find("nfe:prod", namespaces=ns)
            imposto = det.find("nfe:imposto", namespaces=ns)
            p = {
                "codigo":         prod.findtext("nfe:cProd", namespaces=ns) or "",
                "nome":           prod.findtext("nfe:xProd", namespaces=ns) or "",
                "ncm":            prod.findtext("nfe:NCM", namespaces=ns)   or "",
                "cfop":           prod.findtext("nfe:CFOP", namespaces=ns)  or "",
                "unidade":        prod.findtext("nfe:uCom", namespaces=ns)  or "",
                "quantidade":     prod.findtext("nfe:qCom", namespaces=ns)  or "0",
                "valor_unitario": prod.findtext("nfe:vUnCom", namespaces=ns)or "0",
                "valor_total":    prod.findtext("nfe:vProd", namespaces=ns) or "0",
                "impostos": {
                    "icms_valor":   "",
                    "icms_aliquota":"",
                    "pis_valor":    "",
                    "pis_aliquota": "",
                    "cofins_valor": "",
                    "cofins_aliquota":""
                }
            }
            if imposto is not None:
                icms = imposto.find(".//nfe:ICMS//nfe:ICMS00", namespaces=ns)\
                      or imposto.find(".//nfe:ICMS//nfe:ICMS20", namespaces=ns)
                if icms is not None:
                    p["impostos"]["icms_valor"]    = icms.findtext("nfe:vICMS", namespaces=ns) or "0"
                    p["impostos"]["icms_aliquota"] = icms.findtext("nfe:pICMS", namespaces=ns) or "0"
                pis = imposto.find("nfe:PIS/nfe:PISAliq", namespaces=ns)
                if pis is not None:
                    p["impostos"]["pis_valor"]    = pis.findtext("nfe:vPIS", namespaces=ns) or "0"
                    p["impostos"]["pis_aliquota"] = pis.findtext("nfe:pPIS", namespaces=ns) or "0"
                cof = imposto.find("nfe:COFINS/nfe:COFINSAliq", namespaces=ns)
                if cof is not None:
                    p["impostos"]["cofins_valor"]    = cof.findtext("nfe:vCOFINS", namespaces=ns) or "0"
                    p["impostos"]["cofins_aliquota"] = cof.findtext("nfe:pCOFINS", namespaces=ns) or "0"
            produtos.append(p)

        icmstot = root.find(".//nfe:ICMSTot", namespaces=ns)
        totais = {
            "valor_total_produtos": icmstot.findtext("nfe:vProd", namespaces=ns)   or "0",
            "valor_total_nota":     icmstot.findtext("nfe:vNF",  namespaces=ns)   or "0",
            "valor_total_icms":     icmstot.findtext("nfe:vICMS", namespaces=ns)   or "0",
            "valor_total_pis":      icmstot.findtext("nfe:vPIS",  namespaces=ns)   or "0",
            "valor_total_cofins":   icmstot.findtext("nfe:vCOFINS",namespaces=ns)  or "0",
            "valor_total_desconto": icmstot.findtext("nfe:vDesc", namespaces=ns)   or "0"
        } if icmstot is not None else {}

        transp = root.find(".//nfe:transp", namespaces=ns)
        transporte = {
            "modalidade_frete":    transp.findtext("nfe:modFrete", namespaces=ns) or "",
            "quantidade_volumes":  transp.findtext("nfe:vol/nfe:qVol", namespaces=ns) or "0",
            "especie_volumes":     transp.findtext("nfe:vol/nfe:esp", namespaces=ns)  or "",
            "peso_liquido":        transp.findtext("nfe:vol/nfe:pesoL", namespaces=ns) or "0",
            "peso_bruto":          transp.findtext("nfe:vol/nfe:pesoB", namespaces=ns) or "0",
            "transportadora_nome":"",
            "transportadora_cnpj":"",
            "veiculo_placa":"",
            "veiculo_uf":"",
            "veiculo_rntc":""
        }
        if transp is not None:
            tp_node  = transp.find("nfe:transporta", namespaces=ns) # Renomeado para evitar conflito
            veic_node= transp.find("nfe:veicTransp", namespaces=ns) # Renomeado para evitar conflito
            if tp_node:
                transporte["transportadora_nome"] = tp_node.findtext("nfe:xNome", namespaces=ns) or ""
                transporte["transportadora_cnpj"] = tp_node.findtext("nfe:CNPJ", namespaces=ns) or ""
            if veic_node:
                transporte["veiculo_placa"] = veic_node.findtext("nfe:placa", namespaces=ns) or ""
                transporte["veiculo_uf"]    = veic_node.findtext("nfe:UF", namespaces=ns)    or ""
                transporte["veiculo_rntc"]  = veic_node.findtext("nfe:RNTC", namespaces=ns)  or ""

        duplicatas = [
            {
                "numero":     dup.findtext("nfe:nDup",   namespaces=ns) or "",
                "valor":      dup.findtext("nfe:vDup",   namespaces=ns) or "0",
                "vencimento": dup.findtext("nfe:dVenc",  namespaces=ns) or ""
            }
            for dup in root.findall(".//nfe:cobr/nfe:dup", namespaces=ns)
        ]

        info_adicional = root.findtext(".//nfe:infAdic/nfe:infCpl", namespaces=ns) or ""
        chave_acesso   = root.findtext(".//nfe:protNFe/nfe:infProt/nfe:chNFe", namespaces=ns) or ""

        return JsonResponse({
            "nota":           nota,
            "fornecedor":     fornecedor,
            "produtos":       produtos,
            "totais":         totais,
            "transporte":     transporte,
            "duplicatas":     duplicatas,
            "info_adicional": info_adicional,
            "chave_acesso":   chave_acesso
        })

    except Exception as e:
        return JsonResponse({"erro": str(e)}, status=400)
    finally:
        if caminho and os.path.exists(caminho): # Verifica se caminho foi definido
            os.remove(caminho)


@login_required
@csrf_exempt
@require_POST
def salvar_importacao_view(request):
    """
    Salva no banco os dados completos da NFe importada.
    - Cria ou vincula o fornecedor.
    - Cria a nota fiscal com transporte e duplicatas.
    - Cria Produto no catálogo e EntradaProduto.
    - ✅ Cria também os registros de ItemNotaFiscal.
    """
    try:
        import traceback # Movido para dentro do try para escopo local
        # from decimal import Decimal, InvalidOperation # Já importado globalmente

        def converter_data_para_date_local(data_str):
            if not data_str:
                return None
            for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
                try:
                    # Tenta converter de ISO com "T" primeiro, depois formatos comuns
                    return datetime.fromisoformat(data_str.split("T")[0]).date() if "T" in data_str else datetime.strptime(data_str, fmt).date()
                except (ValueError, TypeError):
                    continue
            return None

        def converter_valor_br_local(valor):
            if valor is None or str(valor).strip() == "": # Verifica se é None ou string vazia
                return Decimal("0.00")
            try:
                # Remove espaços, substitui vírgula por ponto
                valor_str = str(valor).strip().replace(",", ".")
                v = Decimal(valor_str)
                # Limita o valor para evitar overflow no banco, se necessário
                # if v > Decimal("99999999.9999999999"):
                #     return Decimal("99999999.9999999999")
                return v
            except InvalidOperation:
                print(f"❌ Erro ao converter valor: {valor}")
                return Decimal("0.00")

        payload = json.loads(request.body.decode("utf-8"))

        nota_data       = payload.get("nota", {})
        fornecedor_data = payload.get("fornecedor", {})
        produtos_data   = payload.get("produtos", [])
        totais_data     = payload.get("totais", {})
        transporte_data = payload.get("transporte", {})
        duplicatas_data = payload.get("duplicatas", [])
        info_adicional  = payload.get("info_adicional", "")
        chave_acesso    = payload.get("chave_acesso", "").strip()

        cnpj = fornecedor_data.get("cnpj")
        if not cnpj:
            return JsonResponse({"erro": "CNPJ do fornecedor não foi informado."}, status=400)

        emp_avancada, _ = EmpresaAvancada.objects.get_or_create(
            cnpj=cnpj,
            defaults={
                "razao_social":  fornecedor_data.get("razao_social", ""),
                "nome_fantasia": fornecedor_data.get("nome_fantasia", ""),
                "logradouro":    fornecedor_data.get("logradouro", ""),
                "numero":        fornecedor_data.get("numero", ""),
                "bairro":        fornecedor_data.get("bairro", ""),
                "cidade":        fornecedor_data.get("municipio", ""),
                "uf":            fornecedor_data.get("uf", ""),
                "cep":           fornecedor_data.get("cep", ""),
                "telefone":      fornecedor_data.get("telefone", ""),
                "status_empresa": "Ativa", # Default status
            }
        )

        if NotaFiscal.objects.filter(chave_acesso=chave_acesso).exists():
            return JsonResponse(
                {"erro": f"Nota fiscal já importada (Chave: {chave_acesso})!"},
                status=400
            )

        nota_fiscal = NotaFiscal.objects.create(
            fornecedor=emp_avancada,
            numero=nota_data.get("numero_nota", ""),
            natureza_operacao=nota_data.get("natureza_operacao", ""),
            data_emissao=converter_data_para_date_local(nota_data.get("data_emissao")),
            data_saida=converter_data_para_date_local(nota_data.get("data_saida")),
            chave_acesso=chave_acesso,
            valor_total_produtos=converter_valor_br_local(totais_data.get("valor_total_produtos")),
            valor_total_nota=converter_valor_br_local(totais_data.get("valor_total_nota")),
            valor_total_icms=converter_valor_br_local(totais_data.get("valor_total_icms")),
            valor_total_pis=converter_valor_br_local(totais_data.get("valor_total_pis")),
            valor_total_cofins=converter_valor_br_local(totais_data.get("valor_total_cofins")),
            valor_total_desconto=converter_valor_br_local(totais_data.get("valor_total_desconto")),
            informacoes_adicionais=info_adicional,
            created_by=request.user,
        )

        if transporte_data:
            TransporteNotaFiscal.objects.create(
                nota_fiscal=nota_fiscal,
                modalidade_frete=transporte_data.get("modalidade_frete"),
                transportadora_nome=transporte_data.get("transportadora_nome"),
                transportadora_cnpj=transporte_data.get("transportadora_cnpj"),
                placa_veiculo=transporte_data.get("veiculo_placa"),
                uf_veiculo=transporte_data.get("veiculo_uf"),
                rntc=transporte_data.get("veiculo_rntc"),
                quantidade_volumes=int(transporte_data.get("quantidade_volumes") or 0),
                especie_volumes=transporte_data.get("especie_volumes"),
                peso_liquido=converter_valor_br_local(transporte_data.get("peso_liquido")),
                peso_bruto=converter_valor_br_local(transporte_data.get("peso_bruto")),
            )

        for dup_data in duplicatas_data: # Renomeado para evitar conflito
            if not dup_data.get("numero"): continue
            DuplicataNotaFiscal.objects.create(
                nota_fiscal=nota_fiscal,
                numero=dup_data.get("numero", ""),
                valor=converter_valor_br_local(dup_data.get("valor")),
                vencimento=converter_data_para_date_local(dup_data.get("vencimento")),
            )

        for prod_data in produtos_data:
            # 🔁 Trata NCM
            ncm_codigo = prod_data.get("ncm", "00000000").strip() or "00000000"
            ncm_obj, _ = NCM.objects.get_or_create(codigo=ncm_codigo)

            # 🔁 Trata unidade de medida (como objeto)
            unidade_str = prod_data.get("unidade", "").strip().upper() or "UN"
            unidade_obj, _ = UnidadeMedida.objects.get_or_create(
                sigla=unidade_str,
                defaults={"descricao": unidade_str}
            )

            # 🔍 Cria ou vincula o produto do catálogo
            codigo_raw = prod_data.get("codigo")
            codigo = str(codigo_raw).strip() if codigo_raw else ""

            if not codigo:
                print(f"❌ Código inválido no item: {json.dumps(prod_data, indent=2, ensure_ascii=False)}")
                return JsonResponse({
                    "erro": "Produto com código vazio ou inválido detectado. Corrija o XML."
                }, status=400)

            produto_obj, _ = Produto.objects.get_or_create(
                codigo=codigo,
                defaults={
                    "nome": prod_data.get("nome"),
                    "ncm": ncm_obj,
                    "unidade_medida": unidade_obj,
                    "preco_venda": converter_valor_br_local(prod_data.get("valor_unitario")),
                    "tipo": "Produto",
                    "controla_estoque": True,
                    "codigo_barras": codigo,  # ← agora usa o mesmo valor limpo
                }
            )


            # ✅ Criação do item da nota fiscal
            ItemNotaFiscal.objects.create(
                nota_fiscal=nota_fiscal,
                codigo=prod_data.get("codigo"),
                descricao=prod_data.get("descricao") or prod_data.get("nome"),  # usa 'descricao' ou 'nome' como fallback
                cfop=prod_data.get("cfop"),
                ncm=prod_data.get("ncm"),  # ← CharField no model
                unidade=unidade_str,
                quantidade=prod_data.get("quantidade") or 0,
                valor_unitario=prod_data.get("valor_unitario") or 0,
                valor_total=prod_data.get("valor_total") or 0,
                icms=prod_data.get("icms") or 0,
                ipi=prod_data.get("ipi") or 0,
                desconto=prod_data.get("desconto") or 0,
            )



            # ✅ Entrada no estoque
            EntradaProduto.objects.create(
                produto=produto_obj,
                fornecedor=emp_avancada,
                quantidade=converter_valor_br_local(prod_data.get("quantidade")),
                preco_unitario=converter_valor_br_local(prod_data.get("valor_unitario")),
                preco_total=converter_valor_br_local(prod_data.get("valor_total")),
                numero_nota=nota_fiscal.numero,
            )

        return JsonResponse({"sucesso": True, "mensagem": "Nota fiscal importada e salva com sucesso!"})

    except Exception as e:
        traceback.print_exc() # Para depuração no console do servidor
        return JsonResponse({"erro": f"Erro ao salvar importação: {str(e)}"}, status=400)


@login_required
def entradas_nota_view(request):
    """Renderiza a página de listagem de notas fiscais com suporte a AJAX, busca e ordenação."""
    notas_qs = NotaFiscal.objects.all()
    termo_busca = request.GET.get("termo", "")
    ordem = request.GET.get("ordem", None) # Padrão para None se não fornecido

    if termo_busca:
        notas_qs = notas_qs.filter(
            Q(numero__icontains=termo_busca) |
            Q(fornecedor__razao_social__icontains=termo_busca)
        )

    # <<<< INÍCIO DA PARTE DE ORDENAÇÃO >>>>
    if ordem:
        campos_permitidos_ordenacao = [
            "numero", "-numero",
            "fornecedor__razao_social", "-fornecedor__razao_social",
            "data_emissao", "-data_emissao",
            "valor_total_nota", "-valor_total_nota" # Adicionado exemplo para valor total
        ]
        if ordem in campos_permitidos_ordenacao:
            notas_qs = notas_qs.order_by(ordem)
        else:
            # Opcional: ordenar por um campo padrão se "ordem" for inválido ou não permitido
            notas_qs = notas_qs.order_by("-data_emissao") 
    else:
        # Ordenação padrão se nenhum parâmetro "ordem" for fornecido
        notas_qs = notas_qs.order_by("-data_emissao")
    # <<<< FIM DA PARTE DE ORDENAÇÃO >>>>

    context = {
        "notas": notas_qs,
        "request": request, # Adicionado para que o template possa aceder ao request.GET.termo
    }

    partial_template = "partials/nota_fiscal/entradas_nota.html"
    base_template = "base.html"

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, partial_template, context)
    
    context["content_template"] = partial_template
    context["data_page"] = "entradas-nota"
    return render(request, base_template, context)


@login_required
def editar_entrada_view(request, pk):
    nota = get_object_or_404(NotaFiscal, pk=pk)
    
    itens_da_nota = nota.itens.all() # Carrega os itens relacionados
    from nota_fiscal.models import TransporteNotaFiscal  # certifique-se que esse import está presente

    try:
        transporte_da_nota = TransporteNotaFiscal.objects.get(nota_fiscal=nota)
    except TransporteNotaFiscal.DoesNotExist:
        transporte_da_nota = None

    duplicatas_da_nota = nota.duplicatas.all() # Carrega as duplicatas relacionadas

    if request.method == "POST":
        form = NotaFiscalForm(request.POST, instance=nota)
        if form.is_valid():
            form.save()
            # Lógica para salvar itens, transporte, duplicatas se forem editáveis aqui
            # Por agora, apenas salvando o formulário principal da nota.
            messages.success(request, "Nota fiscal atualizada com sucesso!") # Adiciona mensagem de sucesso
            # Idealmente, redirecionar para a mesma página de edição ou para a lista
            # return redirect("nome_da_url_de_edicao", pk=nota.pk) ou redirect("nome_da_url_da_lista")
            return JsonResponse({"sucesso": True, "mensagem": "Nota fiscal atualizada com sucesso!", "redirect_url": "/nota-fiscal/entradas/"}) # Mantendo o comportamento original do JSON

        else:
            # Se o formulário não for válido, renderiza a página novamente com os erros
            # e os dados relacionados para que as abas não fiquem vazias.
            context = {
                "form": form,
                "nota": nota,
                "produtos": itens_da_nota,
                "transporte": transporte_da_nota,
                "duplicatas": duplicatas_da_nota,
                "content_template": "partials/nota_fiscal/editar_entrada.html",
                "data_page": "editar-entrada-nota"
            }
            # Para requisições POST inválidas, não é comum retornar JSON diretamente 
            # a menos que o frontend esteja preparado para lidar com isso e atualizar os erros.
            # Se o frontend espera HTML para erros, renderize o template.
            # return render(request, "base.html", context) 
            return JsonResponse({"sucesso": False, "erros": form.errors}, status=400) # Mantendo o comportamento original do JSON para erros
    else:
        form = NotaFiscalForm(instance=nota)
    
    context = {
        "form": form, 
        "nota": nota,
        "produtos": itens_da_nota,       # Adicionado ao contexto
        "transporte": transporte_da_nota, # Adicionado ao contexto
        "duplicatas": duplicatas_da_nota, # Adicionado ao contexto
    }
    partial_template = "partials/nota_fiscal/editar_entrada.html"
    base_template = "base.html"

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        # Para AJAX GET, renderiza apenas o parcial com todos os dados
        return render(request, partial_template, context)
    
    # Para carregamento completo da página (GET normal)
    context["content_template"] = partial_template
    context["data_page"] = "editar-entrada-nota"
    return render(request, base_template, context)


@login_required
@require_POST # Garante que esta view só aceita POST
@csrf_exempt # Se estiver a usar AJAX POST de fora de um form Django, pode precisar, mas idealmente use CSRF token
def excluir_entrada_view(request, pk):
    nota = get_object_or_404(NotaFiscal, pk=pk)
    try:
        nota.delete()
        return JsonResponse({"sucesso": True, "mensagem": "Nota fiscal excluída com sucesso!"})
    except Exception as e:
        return JsonResponse({"sucesso": False, "erro": str(e)}, status=500)

