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
from decimal import Decimal, InvalidOperation

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


from decimal import Decimal, InvalidOperation

@csrf_exempt
@require_POST
def salvar_importacao_view(request):
    """Salva no banco os dados completos da NFe importada, usando EmpresaAvancada como fornecedor."""
    try:
        import json
        from datetime import datetime
        from nota_fiscal.models import NotaFiscal, TransporteNotaFiscal, DuplicataNotaFiscal
        from produto.models import Produto
        from produto.models_entradas import EntradaProduto
        from empresas.models import EmpresaAvancada

        # ————— Conversão de data: ISO (YYYY-MM-DD) ou BR (DD/MM/YYYY) → date
        def converter_data_para_date(data_str):
            if not data_str:
                return None
            # tenta ISO primeiro
            try:
                return datetime.fromisoformat(data_str).date()
            except ValueError:
                pass
            # tenta BR
            try:
                return datetime.strptime(data_str, "%d/%m/%Y").date()
            except ValueError:
                return None

        # ————— Conversão de valor (BR ou US) → Decimal(2 casas)
        def converter_valor_br(valor):
            """
            Recebe:
              - "1.234.567,89" → Decimal('1234567.89')
              - "180.25000000" → Decimal('180.25')
              - números → Decimal(...)
            """
            if valor is None:
                return Decimal('0.00')
            s = str(valor).strip()
            if s.startswith("R$"):
                s = s.replace("R$", "").strip()
            # se tiver vírgula, é BR: remove ponto-milhar e troca vírgula
            if ',' in s:
                s = s.replace('.', '').replace(',', '.')
            # agora s ex: "1234567.89" ou "180.25000000"
            try:
                dec = Decimal(s)
            except InvalidOperation:
                filtered = ''.join(c for c in s if c.isdigit() or c in '.-')
                try:
                    dec = Decimal(filtered)
                except InvalidOperation:
                    return Decimal('0.00')
            return dec.quantize(Decimal('0.01'))

        dados = json.loads(request.body.decode("utf-8"))

        nota_data       = dados.get("nota", {})
        fornecedor_data = dados.get("fornecedor", {})
        produtos_data   = dados.get("produtos", [])
        totais_data     = dados.get("totais", {})
        transporte_data = dados.get("transporte", {})
        duplicatas_data = dados.get("duplicatas", [])
        info_adicional  = dados.get("info_adicional", "")
        chave_acesso    = dados.get("chave_acesso", "").strip()

        # === 1. Fornecedor ===
        fornecedor = None
        if fornecedor_data.get("cnpj"):
            fornecedor, _ = EmpresaAvancada.objects.get_or_create(
                cnpj=fornecedor_data["cnpj"],
                defaults={
                    "razao_social": fornecedor_data.get("razao_social", ""),
                    "nome_fantasia": fornecedor_data.get("nome_fantasia", ""),
                    "logradouro": fornecedor_data.get("logradouro", ""),
                    "numero": fornecedor_data.get("numero", ""),
                    "bairro": fornecedor_data.get("bairro", ""),
                    "cidade": fornecedor_data.get("municipio", ""),
                    "uf": fornecedor_data.get("uf", ""),
                    "cep": fornecedor_data.get("cep", ""),
                    "telefone": fornecedor_data.get("telefone", ""),
                    "status_empresa": "Ativa",
                }
            )

        # === 2. Nota Fiscal (evita duplicata) ===
        if NotaFiscal.objects.filter(chave_acesso=chave_acesso).exists():
            return JsonResponse(
                {"erro": f"Nota fiscal já importada (Chave: {chave_acesso})!"},
                status=400
            )

        nota_fiscal = NotaFiscal.objects.create(
            fornecedor=fornecedor,
            numero=nota_data.get("numero_nota", ""),
            natureza_operacao=nota_data.get("natureza_operacao", ""),
            data_emissao=converter_data_para_date(nota_data.get("data_emissao")),
            data_saida=  converter_data_para_date(nota_data.get("data_saida")),
            chave_acesso=chave_acesso,
            valor_total_produtos=converter_valor_br(totais_data.get("valor_total_produtos")),
            valor_total_nota=    converter_valor_br(totais_data.get("valor_total_nota")),
            valor_total_icms=    converter_valor_br(totais_data.get("valor_total_icms")),
            valor_total_pis=     converter_valor_br(totais_data.get("valor_total_pis")),
            valor_total_cofins=  converter_valor_br(totais_data.get("valor_total_cofins")),
            valor_total_desconto=converter_valor_br(totais_data.get("valor_total_desconto")),
            informacoes_adicionais=info_adicional,
        )

        # === 3. Transporte ===
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

        # === 4. Duplicatas ===
        for dup in duplicatas_data:
            DuplicataNotaFiscal.objects.create(
                nota_fiscal=nota_fiscal,
                numero=dup.get("numero", ""),
                valor=converter_valor_br(dup.get("valor", 0)),
                vencimento=converter_data_para_date(dup.get("vencimento")),
            )

        # === 5. Produtos e Entradas ===
        for p in produtos_data:
            qtd = converter_valor_br(p.get("quantidade"))
            vuni = converter_valor_br(p.get("valor_unitario"))
            vtot = converter_valor_br(p.get("valor_total"))
            impostos = p.get("impostos", {})

            produto_obj = Produto.objects.filter(
                codigo_produto_fornecedor=p.get("codigo")
            ).first()
            if not produto_obj:
                produto_obj = Produto.objects.create(
                    codigo=f"AUTO-{p.get('codigo')}",
                    nome=p.get("nome") or "",
                    descricao=p.get("nome") or "",
                    cfop=p.get("cfop") or "",
                    unidade_comercial=p.get("unidade") or "",
                    codigo_produto_fornecedor=p.get("codigo"),
                    preco_custo=vuni,
                    preco_venda=vuni,
                    preco_medio=vuni,
                    ativo=True,
                )

            EntradaProduto.objects.create(
                produto=produto_obj,
                fornecedor=fornecedor,
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

        return JsonResponse({"mensagem": "Importação salva com sucesso."})

    except Exception as e:
        return JsonResponse({"erro": str(e)}, status=500)
