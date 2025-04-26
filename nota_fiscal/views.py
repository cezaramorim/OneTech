from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import os
import xml.etree.ElementTree as ET
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils.text import slugify

# ✅ Função que renderiza a página de upload (GET)
def importar_xml_view(request):
    return render(request, "partials/nota_fiscal/importar_xml.html")

# ✅ Função que processa o upload (POST via AJAX)
@csrf_exempt
@require_POST
def importar_xml_nfe_view(request):
    """Processa o upload do XML, extrai todos os campos relevantes e retorna JSON estruturado."""
    xml_file = request.FILES.get("xml")

    if not xml_file or not xml_file.name.endswith(".xml"):
        return JsonResponse({"erro": "Arquivo XML inválido."}, status=400)

    try:
        # === [ Salvamento Temporário do Arquivo ]
        nome_seguro = slugify(xml_file.name)
        caminho = os.path.join(settings.MEDIA_ROOT, "xmls_temp", nome_seguro)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)

        with default_storage.open(caminho, "wb+") as destino:
            for chunk in xml_file.chunks():
                destino.write(chunk)

        # === [ Leitura e Parse do XML ]
        tree = ET.parse(caminho)
        root = tree.getroot()
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

        # === [ Dados da Nota Fiscal ]
        infNFe = root.find(".//nfe:infNFe", namespaces=ns)
        nota_data = {}
        if infNFe is not None:
            nota_data = {
                "numero_nota": infNFe.findtext("nfe:ide/nfe:nNF", namespaces=ns),
                "data_emissao": infNFe.findtext("nfe:ide/nfe:dhEmi", namespaces=ns),
                "data_saida": infNFe.findtext("nfe:ide/nfe:dhSaiEnt", namespaces=ns),
                "natureza_operacao": infNFe.findtext("nfe:ide/nfe:natOp", namespaces=ns),
            }

        # === [ Dados do Emitente ]
        emit = root.find(".//nfe:emit", namespaces=ns)
        fornecedor_data = {}
        if emit is not None:
            endereco = emit.find("nfe:enderEmit", namespaces=ns)
            fornecedor_data = {
                "cnpj": emit.findtext("nfe:CNPJ", namespaces=ns),
                "razao_social": emit.findtext("nfe:xNome", namespaces=ns),
                "nome_fantasia": emit.findtext("nfe:xFant", namespaces=ns),
                "logradouro": endereco.findtext("nfe:xLgr", namespaces=ns) if endereco is not None else '',
                "numero": endereco.findtext("nfe:nro", namespaces=ns) if endereco is not None else '',
                "bairro": endereco.findtext("nfe:xBairro", namespaces=ns) if endereco is not None else '',
                "municipio": endereco.findtext("nfe:xMun", namespaces=ns) if endereco is not None else '',
                "uf": endereco.findtext("nfe:UF", namespaces=ns) if endereco is not None else '',
                "cep": endereco.findtext("nfe:CEP", namespaces=ns) if endereco is not None else '',
                "telefone": endereco.findtext("nfe:fone", namespaces=ns) if endereco is not None else '',
                "ie": emit.findtext("nfe:IE", namespaces=ns),
                "crt": emit.findtext("nfe:CRT", namespaces=ns),
            }

        # === [ Produtos da Nota ]
        produtos = []
        for det in root.findall(".//nfe:det", namespaces=ns):
            prod = det.find("nfe:prod", namespaces=ns)
            if prod is not None:
                produtos.append({
                    "codigo": prod.findtext("nfe:cProd", namespaces=ns),
                    "nome": prod.findtext("nfe:xProd", namespaces=ns),
                    "ncm": prod.findtext("nfe:NCM", namespaces=ns),
                    "cfop": prod.findtext("nfe:CFOP", namespaces=ns),
                    "unidade": prod.findtext("nfe:uCom", namespaces=ns),
                    "quantidade": prod.findtext("nfe:qCom", namespaces=ns),
                    "valor_unitario": prod.findtext("nfe:vUnCom", namespaces=ns),
                    "valor_total": prod.findtext("nfe:vProd", namespaces=ns),
                    "valor_desconto": prod.findtext("nfe:vDesc", namespaces=ns) or '0.00',
                    "valor_outros": prod.findtext("nfe:vOutro", namespaces=ns) or '0.00',
                })

        # === [ Totais da Nota ]
        total = root.find(".//nfe:ICMSTot", namespaces=ns)
        totais_data = {}
        if total is not None:
            totais_data = {
                "valor_total_produtos": total.findtext("nfe:vProd", namespaces=ns),
                "valor_total_nota": total.findtext("nfe:vNF", namespaces=ns),
                "valor_total_icms": total.findtext("nfe:vICMS", namespaces=ns),
                "valor_total_pis": total.findtext("nfe:vPIS", namespaces=ns),
                "valor_total_cofins": total.findtext("nfe:vCOFINS", namespaces=ns),
                "valor_total_desconto": total.findtext("nfe:vDesc", namespaces=ns),
            }

        # === [ Transporte da Nota ]
        transp = root.find(".//nfe:transp", namespaces=ns)
        transporte_data = {}
        if transp is not None:
            transporte_data = {
                "modalidade_frete": transp.findtext("nfe:modFrete", namespaces=ns),
                "quantidade_volumes": transp.findtext("nfe:vol/nfe:qVol", namespaces=ns),
                "especie_volumes": transp.findtext("nfe:vol/nfe:esp", namespaces=ns),
                "peso_liquido": transp.findtext("nfe:vol/nfe:pesoL", namespaces=ns),
                "peso_bruto": transp.findtext("nfe:vol/nfe:pesoB", namespaces=ns),
            }
            transporta = transp.find("nfe:transporta", namespaces=ns)
            if transporta is not None:
                transporte_data.update({
                    "transportadora_nome": transporta.findtext("nfe:xNome", namespaces=ns),
                    "transportadora_cnpj": transporta.findtext("nfe:CNPJ", namespaces=ns),
                })
            veic = transp.find("nfe:veicTransp", namespaces=ns)
            if veic is not None:
                transporte_data.update({
                    "veiculo_placa": veic.findtext("nfe:placa", namespaces=ns),
                    "veiculo_uf": veic.findtext("nfe:UF", namespaces=ns),
                    "veiculo_rntc": veic.findtext("nfe:RNTC", namespaces=ns),
                })

        # === [ Duplicatas (Parcelas) ]
        duplicatas = []
        for dup in root.findall(".//nfe:cobr/nfe:dup", namespaces=ns):
            duplicatas.append({
                "numero": dup.findtext("nfe:nDup", namespaces=ns),
                "valor": dup.findtext("nfe:vDup", namespaces=ns),
                "vencimento": dup.findtext("nfe:dVenc", namespaces=ns),
            })

        # === [ Informações Adicionais ]
        infAdic = root.find(".//nfe:infAdic", namespaces=ns)
        info_adicional = infAdic.findtext("nfe:infCpl", namespaces=ns) if infAdic is not None else ""

        # === [ Chave de Acesso ]
        protNFe = root.find(".//nfe:protNFe", namespaces=ns)
        chave_acesso = ""
        if protNFe is not None:
            chave_acesso = protNFe.findtext("nfe:infProt/nfe:chNFe", namespaces=ns)

        # === [ Resposta Final JSON ]
        return JsonResponse({
            "nota": nota_data,
            "fornecedor": fornecedor_data,
            "produtos": produtos,
            "totais": totais_data,
            "transporte": transporte_data,
            "duplicatas": duplicatas,
            "info_adicional": info_adicional,
            "chave_acesso": chave_acesso,
        })

    except Exception as e:
        return JsonResponse({"erro": str(e)}, status=500)