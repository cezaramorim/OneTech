from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.db.models import Q
from .models import Produto, CategoriaProduto, UnidadeMedida, NCM
from .forms import ProdutoForm, CategoriaProdutoForm, UnidadeMedidaForm
from accounts.utils.render import render_ajax_or_base
from django.views.decorators.http import require_GET
import os
import xml.etree.ElementTree as ET
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from django.utils.text import slugify
import xml.etree.ElementTree as ET
import json
from common.utils import formatters

valor = formatters.formatar_numero_br("1234.56")

# =====================
# PRODUTOS
# =====================
@login_required
def lista_produtos_view(request):
    produtos = Produto.objects.all()
    return render_ajax_or_base(request, "partials/produtos/lista_produtos.html", {"produtos": produtos})


@login_required
def cadastrar_produto_view(request):
    if request.method == "POST":
        form = ProdutoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Produto cadastrado com sucesso.")
            return redirect(reverse("produto:lista_produtos"))
    else:
        form = ProdutoForm()
    return render_ajax_or_base(request, "partials/produtos/cadastrar_produto.html", {"form": form})

@login_required
def editar_produto_view(request, pk):
    """
    View para editar um produto existente via AJAX ou GET normal.
    """
    produto = get_object_or_404(Produto, pk=pk)

    if request.method == "POST":
        form = ProdutoForm(request.POST, instance=produto)
        if form.is_valid():
            form.save()
            return JsonResponse({
                "sucesso": True,
                "mensagem": "Produto atualizado com sucesso.",
                "redirect_url": "/produtos/"
            })
        return JsonResponse({"sucesso": False, "erros": form.errors}, status=400)

    form = ProdutoForm(instance=produto)
    context = {
        "form": form,
        "produto": produto,
    }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "partials/produtos/editar_produto.html", context)

    # Se não for AJAX, renderiza com base.html e content_template
    context["content_template"] = "partials/produtos/editar_produto.html"
    context["data_page"] = "editar_produto"
    return render(request, "base.html", context)


@require_POST
@login_required
def excluir_produtos_view(request):
    if not request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"erro": "Requisição inválida."}, status=400)

    try:
        data = json.loads(request.body.decode("utf-8"))
        ids = data.get("ids", [])
        if not ids:
            return JsonResponse({"erro": "Nenhum produto selecionado."}, status=400)

        Produto.objects.filter(id__in=ids).delete()
        return JsonResponse({"sucesso": True, "mensagem": "Produtos excluídos com sucesso."})

    except Exception as e:
        return JsonResponse({"erro": f"Erro ao excluir: {str(e)}"}, status=500)


# ======================
# CATEGORIAS DE PRODUTOS
# ======================
@login_required
def lista_categorias_view(request):
    categorias = CategoriaProduto.objects.all()
    return render_ajax_or_base(
        request,
        "partials/produtos/lista_categorias.html",
        {
            "categorias": categorias,
            "data_tela": "lista_categorias",  # ✅ Adicionado aqui
            "data_page": "lista_categorias",
        }
    )
    
@login_required
def editar_categoria_view(request, pk):
    categoria = get_object_or_404(CategoriaProduto, pk=pk)
    if request.method == "POST":
        form = CategoriaProdutoForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": True, "message": "Categoria atualizada com sucesso.", "redirect_url": reverse("produto:lista_categorias")})
    else:
        form = CategoriaProdutoForm(instance=categoria)

    context = {"form": form, "categoria": categoria,}
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "partials/produtos/editar_categoria.html", context)

    return render(request, "base.html", {
        "content_template": "partials/produtos/lista_categorias.html",
        **context,
    })

@require_POST
@login_required
def excluir_categorias_view(request):
    """
    Exclui múltiplas categorias de produto via AJAX.
    """
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        try:
            body = json.loads(request.body)
            ids = body.get("ids", [])
            CategoriaProduto.objects.filter(id__in=ids).delete()
            return JsonResponse({"sucesso": True, "mensagem": "Categorias excluídas com sucesso."})
        except Exception as e:
            return JsonResponse({"erro": f"Erro ao excluir categorias: {str(e)}"}, status=500)
    return JsonResponse({"erro": "Requisição inválida."}, status=400)

@login_required
def cadastrar_categoria_view(request):
    if request.method == "POST":
        form = CategoriaProdutoForm(request.POST)
        if form.is_valid():
            form.save()
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({
                    "sucesso": True,
                    "mensagem": "Categoria cadastrada com sucesso.",
                    "redirect_url": reverse("produto:lista_categorias")
                })
            else:
                messages.success(request, "Categoria cadastrada com sucesso.")
                return redirect("produto:lista_categorias")
        else:
            # Tratamento de erro para AJAX
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                erros = []
                for field, msgs in form.errors.items():
                    for msg in msgs:
                        label = form.fields[field].label
                        erros.append(f"{label}: {msg}")
                return JsonResponse({
                    "sucesso": False,
                    "mensagem": "Erro ao salvar categoria:<br>" + "<br>".join(erros)
                }, status=400)

    else:
        form = CategoriaProdutoForm()

    return render_ajax_or_base(
        request,
        "partials/produtos/cadastrar_categoria.html",
        {"form": form, "data_tela": "cadastrar_categoria"}
    )



# =====================
# UNIDADES
# =====================
@login_required
def lista_unidades_view(request):
    unidades = UnidadeMedida.objects.all()
    return render_ajax_or_base(request, "partials/produtos/lista_unidades.html", {"unidades": unidades})


@login_required
def cadastrar_unidade_view(request):
    if request.method == "POST":
        form = UnidadeMedidaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Unidade cadastrada com sucesso.")
            return redirect(reverse("produto:lista_unidades"))
    else:
        form = UnidadeMedidaForm()
    return render_ajax_or_base(request, "partials/produtos/cadastrar_unidade.html", {"form": form})

def is_superuser_or_staff(user):
    return user.is_superuser or user.is_staff

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def manutencao_ncm_view(request):
    termo = request.GET.get("term", "").strip()
    ncm_lista = NCM.objects.all()

    if termo:
        ncm_lista = ncm_lista.filter(
            Q(codigo__icontains=termo) | Q(descricao__icontains=termo)
        ).order_by("codigo")[:20]
    else:
        ncm_lista = ncm_lista.order_by("codigo")

    context = {
        "ncm_lista": ncm_lista,
    }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        if termo:
            # 🔄 Pesquisa → atualiza só a tabela
            return render(request, "partials/produtos/tabela_ncm.html", context)
        else:
            # 🔁 Termo vazio → recarrega tela completa (com campo e botão)
            return render(request, "partials/produtos/manutencao_ncm.html", context)

    # 🟦 Primeira carga padrão (não-AJAX)
    return render(request, "base.html", {
        "content_template": "partials/produtos/manutencao_ncm.html",
        "ncm_lista": ncm_lista,
    })



def buscar_ncm_ajax(request):
    termo = request.GET.get('term', '')
    resultados = []

    if termo:
        qs = NCM.objects.filter(descricao__icontains=termo)[:20]
        resultados = [{"id": ncm.codigo, "text": f"{ncm.codigo} - {ncm.descricao}"} for ncm in qs]

    return JsonResponse({"results": resultados})


@login_required
@user_passes_test(is_superuser_or_staff)
def importar_ncm_manual_view(request):
    import json, requests
    try:
        url = "https://portalunico.siscomex.gov.br/classif/api/publico/nomenclatura/download/json"
        response = requests.get(url)
        data = response.json()
        if isinstance(data, str):
            data = json.loads(data)
        count = 0
        for item in data:
            if '|' in item:
                codigo, descricao = item.split('|', 1)
                NCM.objects.update_or_create(codigo=codigo.strip(), defaults={"descricao": descricao.strip()})
                count += 1
        return JsonResponse({"status": "ok", "mensagem": f"{count} códigos NCM importados com sucesso."})
    except Exception as e:
        return JsonResponse({"status": "erro", "mensagem": str(e)}, status=500)


@csrf_exempt
@require_POST
def importar_xml_nfe_view(request):
    """
    View para upload e leitura de XML da NFe.
    Retorna os dados do emitente e lista de produtos da nota.
    """
    xml_file = request.FILES.get("xml")

    if not xml_file or not xml_file.name.endswith(".xml"):
        return JsonResponse({"erro": "Arquivo XML inválido."}, status=400)

    try:
        # Salvamento temporário
        nome_seguro = slugify(xml_file.name)
        caminho = os.path.join(settings.MEDIA_ROOT, "xmls_temp", nome_seguro)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)

        with default_storage.open(caminho, "wb+") as destino:
            for chunk in xml_file.chunks():
                destino.write(chunk)

        # Parse do XML
        tree = ET.parse(caminho)
        root = tree.getroot()

        # Emitente (fornecedor)
        emit = root.find(".//emit")
        fornecedor_data = {
            "cnpj": emit.findtext("CNPJ"),
            "razao_social": emit.findtext("xNome")
        } if emit is not None else {}

        # Produtos (múltiplos <det>)
        produtos = []
        for det in root.findall(".//det"):
            prod = {
                "codigo": det.findtext(".//cProd"),
                "nome": det.findtext(".//xProd"),
                "ncm": det.findtext(".//NCM"),
                "cfop": det.findtext(".//CFOP"),
            }
            produtos.append(prod)

        return JsonResponse({
            "fornecedor": fornecedor_data,
            "produtos": produtos
        })

    except Exception as e:
        return JsonResponse({"erro": str(e)}, status=500)


@login_required
def importar_xml_view(request):
    return render(request, "partials/nota_fiscal/importar_xml.html")


@require_GET
def buscar_ncm_descricao_ajax(request):
    """
    View para autocomplete do campo NCM no cadastro de produto.
    Retorna uma lista de objetos JSON com 'id' e 'text'.
    """
    termo = request.GET.get('term', '').strip()
    resultados = []

    if termo:
        ncm_qs = NCM.objects.filter(
            Q(codigo__icontains=termo) | Q(descricao__icontains=termo)
        ).order_by("codigo")[:20]

        resultados = [
            {"id": ncm.codigo, "text": f"{ncm.codigo} - {ncm.descricao}"}
            for ncm in ncm_qs
        ]

    return JsonResponse({"results": resultados})
