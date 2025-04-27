from datetime import datetime
import os
import json
import xml.etree.ElementTree as ET
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.utils.text import slugify
from django.conf import settings

from nota_fiscal.models import NotaFiscal, TransporteNotaFiscal, DuplicataNotaFiscal
from produto.models import Produto
from produto.models_entradas import EntradaProduto
from empresas.models import EmpresaAvancada


def importar_xml_view(request):
    """Renderiza a página de upload de XML."""
    return render(request, "partials/nota_fiscal/importar_xml.html")


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


@csrf_exempt
@require_POST
def salvar_importacao_view(request):
    """
    Salva no banco os dados completos da NFe importada.
    Se a chave_acesso já existir, retorna 400 + mensagem de erro.
    """
    try:
        dados = json.loads(request.body.decode("utf-8"))
        chave = dados.get("chave_acesso", "").strip()

        # — se já importada → erro 400
        if NotaFiscal.objects.filter(chave_acesso=chave).exists():
            return JsonResponse(
                {"erro": f"Nota fiscal já importada (Chave: {chave})!"},
                status=400
            )

        # — caso contrário, converte e salva tudo:
        def conv_date(s):  # ISO ou BR → date
            try:
                return datetime.fromisoformat(s).date()
            except Exception:
                try:
                    return datetime.strptime(s, "%d/%m/%Y").date()
                except Exception:
                    return None

        def conv_val(v):  # "R$ 1.234,56" → float
            if not v: return 0
            return float(str(v).replace("R$", "").replace(".", "").replace(",", ".").strip())

        # 1) fornecedor
        f = dados["fornecedor"]
        empresa, _ = EmpresaAvancada.objects.get_or_create(
            cnpj=f.get("cnpj"),
            defaults={
                "razao_social": f.get("razao_social", ""),
                "nome_fantasia": f.get("nome_fantasia", ""),
                "logradouro": f.get("logradouro", ""),
                "numero": f.get("numero", ""),
                "bairro": f.get("bairro", ""),
                "cidade": f.get("municipio", ""),
                "uf": f.get("uf", ""),
                "cep": f.get("cep", ""),
                "telefone": f.get("telefone", ""),
                "status_empresa": "Ativa",
            }
        )

        # 2) nota fiscal
        n = dados["nota"]
        nota = NotaFiscal.objects.create(
            fornecedor=empresa,
            numero=n.get("numero_nota", ""),
            natureza_operacao=n.get("natureza_operacao", ""),
            data_emissao=conv_date(n.get("data_emissao","")),
            data_saida=  conv_date(n.get("data_saida","")),
            chave_acesso=chave,
            valor_total_produtos=conv_val(dados["totais"].get("valor_total_produtos","0")),
            valor_total_nota=    conv_val(dados["totais"].get("valor_total_nota","0")),
            valor_total_icms=    conv_val(dados["totais"].get("valor_total_icms","0")),
            valor_total_pis=     conv_val(dados["totais"].get("valor_total_pis","0")),
            valor_total_cofins=  conv_val(dados["totais"].get("valor_total_cofins","0")),
            valor_total_desconto=conv_val(dados["totais"].get("valor_total_desconto","0")),
            informacoes_adicionais=dados.get("info_adicional",""),
        )

        # 3) transporte
        t = dados["transporte"]
        TransporteNotaFiscal.objects.create(
            nota_fiscal=nota,
            modalidade_frete=t.get("modalidade_frete",""),
            transportadora_nome=t.get("transportadora_nome",""),
            transportadora_cnpj=t.get("transportadora_cnpj",""),
            placa_veiculo=t.get("veiculo_placa",""),
            uf_veiculo=t.get("veiculo_uf",""),
            rntc=t.get("veiculo_rntc",""),
            quantidade_volumes=int(t.get("quantidade_volumes") or 0),
            especie_volumes=t.get("especie_volumes",""),
            peso_liquido=float(t.get("peso_liquido") or 0),
            peso_bruto=float(t.get("peso_bruto") or 0),
        )

        # 4) duplicatas
        for dup in dados["duplicatas"]:
            DuplicataNotaFiscal.objects.create(
                nota_fiscal=nota,
                numero=dup.get("numero", ""),
                valor=conv_val(dup.get("valor","0")),
                vencimento=conv_date(dup.get("vencimento","")),
            )

        # 5) produtos e entradas
        for p in dados["produtos"]:
            produto = Produto.objects.filter(codigo_produto_fornecedor=p["codigo"]).first()
            if not produto:
                produto = Produto.objects.create(
                    codigo=f"AUTO-{p['codigo']}",
                    nome=p.get("nome",""),
                    descricao=p.get("nome",""),
                    cfop=p.get("cfop",""),
                    unidade_comercial=p.get("unidade",""),
                    quantidade_comercial=float(p.get("quantidade") or 0),
                    preco_custo=conv_val(p.get("valor_unitario","0")),
                    preco_venda=conv_val(p.get("valor_unitario","0")),
                    preco_medio=conv_val(p.get("valor_unitario","0")),
                    codigo_produto_fornecedor=p.get("codigo",""),
                    ativo=True,
                )
            EntradaProduto.objects.create(
                produto=produto,
                fornecedor=empresa,
                quantidade=float(p.get("quantidade") or 0),
                preco_unitario=conv_val(p.get("valor_unitario","0")),
                preco_total=conv_val(p.get("valor_total","0")),
                numero_nota=nota.numero,
                icms_valor=conv_val(p["impostos"].get("icms_valor","0")),
                icms_aliquota=conv_val(p["impostos"].get("icms_aliquota","0")),
                pis_valor=conv_val(p["impostos"].get("pis_valor","0")),
                pis_aliquota=conv_val(p["impostos"].get("pis_aliquota","0")),
                cofins_valor=conv_val(p["impostos"].get("cofins_valor","0")),
                cofins_aliquota=conv_val(p["impostos"].get("cofins_aliquota","0")),
            )

        return JsonResponse({"mensagem": "Importação salva com sucesso."})

    except Exception as e:
        return JsonResponse({"erro": str(e)}, status=500)
