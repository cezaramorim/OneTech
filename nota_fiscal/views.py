# nota_fiscal/views.py

import os
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
import xml.etree.ElementTree as ET
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
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


from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def importar_xml_view(request):
    """Renderiza a página de upload de XML com suporte a AJAX e carregamento completo."""
    partial = "partials/nota_fiscal/importar_xml.html"
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, partial)
    return render(request, "base.html", {
        "content_template": partial,
        "data_page": "importar_xml"
    })


@login_required                      # ← só permite usuários logados
@csrf_exempt                        # ← mantém isenção de CSRF (para sua API AJAX)
@require_POST                       # ← aceita somente POST
def importar_xml_nfe_view(request):
    """
    Processa upload de XML da NFe e retorna JSON com TODOS os campos
    (nota, fornecedor, produtos, totais, transporte, duplicatas, info_adicional, chave_acesso),
    mantendo as datas em ISO (YYYY-MM-DD).
    """
    xml_file = request.FILES.get("xml")
    if not xml_file or not xml_file.name.lower().endswith(".xml"):
        return JsonResponse({"erro": "Arquivo XML inválido."}, status=400)

    try:
        # Salva temporário
        nome_seguro = slugify(xml_file.name)
        caminho = os.path.join(settings.MEDIA_ROOT, "xmls_temp", nome_seguro)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with default_storage.open(caminho, "wb+") as destino:
            for chunk in xml_file.chunks():
                destino.write(chunk)

        # Parse XML
        tree = ET.parse(caminho)
        root = tree.getroot()
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

        # Extrai datas (ISO YYYY-MM-DD)
        raw_dhEmi    = root.findtext(".//nfe:ide/nfe:dhEmi", namespaces=ns) or ""
        raw_dEmi     = root.findtext(".//nfe:ide/nfe:dEmi",  namespaces=ns) or ""
        raw_dhSaiEnt = root.findtext(".//nfe:ide/nfe:dhSaiEnt", namespaces=ns) or ""
        raw_dSaiEnt  = root.findtext(".//nfe:ide/nfe:dSaiEnt",  namespaces=ns) or ""
        data_emissao = (raw_dhEmi or raw_dEmi).split("T")[0] if (raw_dhEmi or raw_dEmi) else ""
        data_saida   = (raw_dhSaiEnt or raw_dSaiEnt).split("T")[0] if (raw_dhSaiEnt or raw_dSaiEnt) else ""

        # === Montagem do JSON de resposta ===
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
            tp  = transp.find("nfe:transporta", namespaces=ns)
            veic= transp.find("nfe:veicTransp", namespaces=ns)
            if tp:
                transporte["transportadora_nome"] = tp.findtext("nfe:xNome", namespaces=ns) or ""
                transporte["transportadora_cnpj"] = tp.findtext("nfe:CNPJ", namespaces=ns) or ""
            if veic:
                transporte["veiculo_placa"] = veic.findtext("nfe:placa", namespaces=ns) or ""
                transporte["veiculo_uf"]    = veic.findtext("nfe:UF", namespaces=ns)    or ""
                transporte["veiculo_rntc"]  = veic.findtext("nfe:RNTC", namespaces=ns)  or ""

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
    from produto.models_entradas import EntradaProduto
    try:
        import traceback
        from decimal import Decimal, InvalidOperation

        def converter_data_para_date(data_str):
            if not data_str:
                return None
            for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
                try:
                    return datetime.fromisoformat(data_str).date() if "T" in data_str else datetime.strptime(data_str, fmt).date()
                except Exception:
                    continue
            return None

        def converter_valor_br(valor):
            if not valor:
                return Decimal("0.0")
            try:
                v = Decimal(str(valor).strip().replace(",", "."))
                if v > Decimal('99999999.9999999999'):
                    return Decimal('99999999.9999999999')
                return v
            except InvalidOperation:
                print("❌ Erro ao converter valor:", valor)
                return Decimal("0.0")

        payload = json.loads(request.body.decode("utf-8"))
        print("📦 Dados recebidos:", json.dumps(payload, indent=2, ensure_ascii=False))

        nota_data       = payload.get("nota", {})
        fornecedor_data = payload.get("fornecedor", {})
        produtos_data   = payload.get("produtos", [])
        totais_data     = payload.get("totais", {})
        transporte_data = payload.get("transporte", {})
        duplicatas_data = payload.get("duplicatas", [])
        info_adicional  = payload.get("info_adicional", "")
        chave_acesso    = payload.get("chave_acesso", "").strip()

        # 1) Fornecedor (emitente)
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
                "status_empresa": "Ativa",
            }
        )

        # 2) Evita duplicata
        if NotaFiscal.objects.filter(chave_acesso=chave_acesso).exists():
            return JsonResponse(
                {"erro": f"Nota fiscal já importada (Chave: {chave_acesso})!"},
                status=400
            )

        # 3) Cria Nota Fiscal
        nota_fiscal = NotaFiscal.objects.create(
            fornecedor=emp_avancada,
            numero=nota_data.get("numero_nota", ""),
            natureza_operacao=nota_data.get("natureza_operacao", ""),
            data_emissao=converter_data_para_date(nota_data.get("data_emissao")),
            data_saida=converter_data_para_date(nota_data.get("data_saida")),
            chave_acesso=chave_acesso,
            valor_total_produtos=converter_valor_br(totais_data.get("valor_total_produtos")),
            valor_total_nota=converter_valor_br(totais_data.get("valor_total_nota")),
            valor_total_icms=converter_valor_br(totais_data.get("valor_total_icms")),
            valor_total_pis=converter_valor_br(totais_data.get("valor_total_pis")),
            valor_total_cofins=converter_valor_br(totais_data.get("valor_total_cofins")),
            valor_total_desconto=converter_valor_br(totais_data.get("valor_total_desconto")),
            informacoes_adicionais=info_adicional,
            created_by=request.user,
        )

        # 4) Transporte
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
                peso_liquido=converter_valor_br(transporte_data.get("peso_liquido")),
                peso_bruto=converter_valor_br(transporte_data.get("peso_bruto")),
            )

        # 5) Duplicatas
        for dup in duplicatas_data:
            if not dup.get("numero"): continue
            DuplicataNotaFiscal.objects.create(
                nota_fiscal=nota_fiscal,
                numero=dup.get("numero", ""),
                valor=converter_valor_br(dup.get("valor", 0)),
                vencimento=converter_data_para_date(dup.get("vencimento")),
            )


        # 6) Produtos e Itens da Nota — com agrupamento por código
        produtos_agrupados = {}

        for p in produtos_data:
            codigo = (p.get("codigo") or "").strip()
            nome = p.get("nome", "").strip()
            if not codigo or not nome:
                print("❌ Produto inválido:", p)
                continue

            if codigo not in produtos_agrupados:
                produtos_agrupados[codigo] = p.copy()
            else:
                # Agrupa somando quantidade e valor_total
                produtos_agrupados[codigo]["quantidade"] = str(
                    Decimal(produtos_agrupados[codigo].get("quantidade", "0")) + Decimal(p.get("quantidade", "0"))
                )
                produtos_agrupados[codigo]["valor_total"] = str(
                    Decimal(produtos_agrupados[codigo].get("valor_total", "0")) + Decimal(p.get("valor_total", "0"))
                )

        # 🔁 Agora salva os itens agrupados
        for p in produtos_agrupados.values():
            codigo = (p.get("codigo") or "").strip()
            nome = p.get("nome", "").strip()
            if not codigo or not nome:
                continue

            qtd = converter_valor_br(p.get("quantidade"))
            vuni = converter_valor_br(p.get("valor_unitario"))
            vtot = converter_valor_br(p.get("valor_total"))
            impostos = p.get("impostos", {})

            # Cria ou atualiza Produto (catálogo)
            produto_obj, _ = Produto.objects.update_or_create(
                codigo=f"AUTO-{codigo}",
                defaults={
                    "nome": nome,
                    "descricao": nome,
                    "cfop": p.get("cfop") or "",
                    "unidade_comercial": p.get("unidade") or "",
                    "codigo_produto_fornecedor": codigo,
                    "preco_custo": vuni,
                    "preco_venda": vuni,
                    "preco_medio": vuni,
                    "estoque_total": qtd,
                    "quantidade_saidas": Decimal("0.0"),
                    "estoque_atual": qtd,
                    "controla_estoque": True,
                    "ativo": True,
                    "data_cadastro": timezone.now().date(),
                    "fornecedor": emp_avancada
                }
            )

            # Cria EntradaProduto (estoque)
            EntradaProduto.objects.create(
                produto=produto_obj,
                fornecedor=emp_avancada,
                quantidade=qtd,
                preco_unitario=vuni,
                preco_total=vtot,
                numero_nota=nota_fiscal.numero,
                icms_valor=converter_valor_br(impostos.get("icms_valor")),
                icms_aliquota=converter_valor_br(impostos.get("icms_aliquota")),
                pis_valor=converter_valor_br(impostos.get("pis_valor")),
                pis_aliquota=converter_valor_br(impostos.get("pis_aliquota")),
                cofins_valor=converter_valor_br(impostos.get("cofins_valor")),
                cofins_aliquota=converter_valor_br(impostos.get("cofins_aliquota")),
            )

            # Cria ItemNotaFiscal
            ItemNotaFiscal.objects.create(
                nota_fiscal=nota_fiscal,
                produto=produto_obj,
                codigo=codigo,
                descricao=nome,
                ncm=p.get("ncm", ""),
                cfop=p.get("cfop", ""),
                unidade=p.get("unidade", ""),
                quantidade=qtd,
                valor_unitario=vuni,
                valor_total=vtot,
                icms=converter_valor_br(impostos.get("icms_valor")),
                ipi=Decimal("0.0"),  # ajuste se necessário
                desconto=Decimal("0.0"),  # ajuste se necessário
            )

        
        
       
        return JsonResponse({"mensagem": "Importação salva com sucesso."})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"erro": f"Erro interno: {str(e)}"}, status=500)


# nota_fiscal/views.py
@login_required
def editar_entrada_view(request, pk):
    """
    Exibe o formulário de edição de nota fiscal (entrada),
    com as abas de dados, produtos, transporte e duplicatas.
    """
    nota = get_object_or_404(NotaFiscal, pk=pk)
    produtos = EntradaProduto.objects.filter(numero_nota=nota.numero)
    transporte = TransporteNotaFiscal.objects.filter(nota_fiscal=nota).first()
    duplicatas = DuplicataNotaFiscal.objects.filter(nota_fiscal=nota)

    form = NotaFiscalForm(instance=nota)

    context = {
        'form': form,
        'nota': nota,
        'produtos': produtos,
        'transporte': transporte,
        'duplicatas': duplicatas,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'partials/nota_fiscal/editar_entrada.html', context)
    return render(request, 'base.html', {
        'content_template': 'partials/nota_fiscal/editar_entrada.html',
        **context,
    })

# nota_fiscal/views.py (adicionar ao final do arquivo)

from django.contrib.auth.decorators import user_passes_test

# nota_fiscal/views.py
from django.db.models import Q

@login_required
def entradas_nota_view(request):
    """
    Lista notas fiscais com suporte a AJAX, filtro por termo (número ou razão social)
    e ordenação dinâmica por campos (número, fornecedor, data de emissão).
    """
    termo = request.GET.get("termo", "").strip()
    ordenar_por = request.GET.get("ordenar", "data_emissao")
    ordem = request.GET.get("ordem", "desc")

    # 🔍 Base da consulta
    notas = NotaFiscal.objects.select_related("fornecedor", "created_by")

    # 🔎 Filtro por termo
    if termo:
        notas = notas.filter(
            Q(numero__icontains=termo) |
            Q(fornecedor__razao_social__icontains=termo)
        )

    # ↕️ Ordenação dinâmica segura
    campos_validos = ["numero", "fornecedor__razao_social", "data_emissao"]
    if ordenar_por in campos_validos:
        if ordem == "desc":
            ordenar_por = "-" + ordenar_por
        notas = notas.order_by(ordenar_por)
    else:
        notas = notas.order_by("-data_emissao")

    context = {"notas": notas}

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "partials/nota_fiscal/entradas_nota.html", context)

    return render(request, "base.html", {
        "content_template": "partials/nota_fiscal/entradas_nota.html",
        **context,
    })

@login_required
@require_POST
def excluir_entrada_view(request, pk):
    """
    Exclui uma nota fiscal e todos os dados vinculados a ela:
    transporte, duplicatas, itens da nota, entradas de estoque e produtos vinculados.
    """
    nota = get_object_or_404(NotaFiscal, pk=pk)

    try:
        # Exclui itens da nota
        ItemNotaFiscal.objects.filter(nota_fiscal=nota).delete()

        # Exclui entradas de estoque
        EntradaProduto.objects.filter(numero_nota=nota.numero).delete()

        # Exclui produtos vinculados diretamente à nota
        Produto.objects.filter(nota_fiscal=nota).delete()

        # Exclui transporte e duplicatas
        TransporteNotaFiscal.objects.filter(nota_fiscal=nota).delete()
        DuplicataNotaFiscal.objects.filter(nota_fiscal=nota).delete()

        # Por fim, exclui a nota
        nota.delete()

        return JsonResponse({"mensagem": "Nota fiscal e dados relacionados excluídos com sucesso."})

    except Exception as e:
        return JsonResponse({"erro": f"Erro ao excluir: {str(e)}"}, status=500)
