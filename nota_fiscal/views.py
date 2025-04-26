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

@login_required
def importar_xml_view(request):
    """Exibe o formulário de upload."""
    return render(request, "partials/nota_fiscal/importar_xml.html")

@csrf_exempt
@require_POST
def importar_xml_nfe_view(request):
    """Processa o upload do XML."""
    xml_file = request.FILES.get("xml")

    if not xml_file or not xml_file.name.endswith(".xml"):
        return JsonResponse({"erro": "Arquivo XML inválido."}, status=400)

    try:
        nome_seguro = slugify(xml_file.name)
        caminho = os.path.join(settings.MEDIA_ROOT, "xmls_temp", nome_seguro)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)

        with default_storage.open(caminho, "wb+") as destino:
            for chunk in xml_file.chunks():
                destino.write(chunk)

        tree = ET.parse(caminho)
        root = tree.getroot()

        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}  # ✅ Definir namespace

        emit = root.find(".//nfe:emit", namespaces=ns)
        fornecedor_data = {
            "cnpj": emit.findtext("nfe:CNPJ", namespaces=ns),
            "razao_social": emit.findtext("nfe:xNome", namespaces=ns),
        } if emit is not None else {}

        produtos = []
        for det in root.findall(".//nfe:det", namespaces=ns):
            prod = det.find("nfe:prod", namespaces=ns)
            if prod is not None:
                produtos.append({
                    "codigo": prod.findtext("nfe:cProd", namespaces=ns),
                    "nome": prod.findtext("nfe:xProd", namespaces=ns),
                    "ncm": prod.findtext("nfe:NCM", namespaces=ns),
                    "cfop": prod.findtext("nfe:CFOP", namespaces=ns),
                })

        return JsonResponse({
            "fornecedor": fornecedor_data,
            "produtos": produtos,
        })

    except Exception as e:
        return JsonResponse({"erro": str(e)}, status=500)
