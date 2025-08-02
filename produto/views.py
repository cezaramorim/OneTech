import json
from django.db.models import Q
from django.contrib import messages
from common.messages_utils import get_app_messages
from django.urls import reverse
from django.forms import inlineformset_factory
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from .forms import ProdutoForm, CategoriaProdutoForm, UnidadeMedidaForm, DetalhesFiscaisProdutoForm
from .models import Produto, CategoriaProduto, UnidadeMedida, NCM, DetalhesFiscaisProduto
from common.utils import render_ajax_or_base

DetalhesFiscaisProdutoFormSet = inlineformset_factory(
    Produto, 
    DetalhesFiscaisProduto, 
    form=DetalhesFiscaisProdutoForm, 
    fields='__all__', 
    can_delete=False, 
    extra=1, 
    max_num=1
)

# =====================
# PRODUTOS
# =====================
@login_required
def lista_produtos_view(request):
    produtos = Produto.objects.all()
    return render_ajax_or_base(request, "partials/produtos/lista_produtos.html", {"produtos": produtos})


@login_required
def cadastrar_produto_view(request):
    app_messages = get_app_messages(request)
    if request.method == "POST":
        form = ProdutoForm(request.POST)
        formset = DetalhesFiscaisProdutoFormSet(request.POST, instance=form.instance)

        if form.is_valid() and formset.is_valid():
            produto = form.save()
            detalhes_fiscais = formset.save(commit=False)
            for df in detalhes_fiscais:
                df.produto = produto
                df.save()
            app_messages.success_created(produto)
            return redirect(reverse("produto:lista_produtos"))
        else:
            app_messages.error("Erro ao cadastrar produto. Verifique os campos.")
    else:
        form = ProdutoForm()
        formset = DetalhesFiscaisProdutoFormSet(instance=Produto())

    return render_ajax_or_base(request, "partials/produtos/cadastrar_produto.html", {"form": form, "formset": formset})

@login_required
def editar_produto_view(request, pk):
    app_messages = get_app_messages(request)
    """
    View para editar um produto existente via AJAX ou GET normal.
    """
    print(f"DEBUG: editar_produto_view - PK recebido: {pk}")
    produto = get_object_or_404(Produto, pk=pk)
    print(f"DEBUG: editar_produto_view - Produto encontrado: {produto.nome}")

    if request.method == "POST":
        form = ProdutoForm(request.POST, instance=produto)
        formset = DetalhesFiscaisProdutoFormSet(request.POST, instance=produto)

        if form.is_valid() and formset.is_valid():
            print("Formulário de Produto é válido.")
            print("Form.cleaned_data:", form.cleaned_data)
            produto = form.save()
            formset.save()
            message = app_messages.success_updated(produto)
            return JsonResponse({
                "success": True,
                "message": message,
                "redirect_url": reverse("produto:lista_produtos")
            })
        else:
            print("Formulário de Produto NÃO é válido.")
            print("Form.errors:", form.errors)
            message = app_messages.error("Erro ao atualizar produto. Verifique os campos.")
            return JsonResponse({"success": False, "message": message, "errors": form.errors, "formset_errors": formset.errors}, status=400)

    form = ProdutoForm(instance=produto)
    formset = DetalhesFiscaisProdutoFormSet(instance=produto)
    context = {
        "form": form,
        "formset": formset,
        "produto": produto,
        "icms_isento_cst": '40,41,50,51',
        "icms_isento_csosn": '103,300,400',
        "ipi_isento_cst": '51',
        "pis_cofins_isento_cst": '04,05,06,07,08,09',
    }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "partials/produtos/editar_produto.html", context)

    # Se não for AJAX, renderiza com base.html e content_template
    context["content_template"] = "partials/produtos/editar_produto.html"
    context["data_page"] = "editar_produto"
    return render(request, "base.html", context)


@require_POST
@login_required
def excluir_produtos_multiplos_view(request):
    app_messages = get_app_messages(request)
    if not request.headers.get("x-requested-with") == "XMLHttpRequest":
        message = app_messages.error("Requisição inválida.")
        return JsonResponse({"success": False, "message": message}, status=400)

    try:
        data = json.loads(request.body.decode("utf-8"))
        ids = data.get("ids", [])
        if not ids:
            message = app_messages.error("Nenhum produto selecionado.")
            return JsonResponse({"success": False, "message": message}, status=400)

        count = len(ids)
        Produto.objects.filter(id__in=ids).delete()
        message = app_messages.success_deleted("Produto(s)", f"{count} selecionado(s)")
        return JsonResponse({"success": True, "message": message})

    except Exception as e:
        message = app_messages.error(f"Erro ao excluir: {str(e)}")
        return JsonResponse({"success": False, "message": message}, status=500)


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
    app_messages = get_app_messages(request)
    print(f"DEBUG: editar_categoria_view - PK recebido: {pk}")
    categoria = get_object_or_404(CategoriaProduto, pk=pk)
    print(f"DEBUG: editar_categoria_view - Categoria encontrada: {categoria.nome}")
    if request.method == "POST":
        form = CategoriaProdutoForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            message = app_messages.success_updated(categoria)
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": True, "message": message, "redirect_url": reverse("produto:lista_categorias")})
        else:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                message = app_messages.error("Erro ao salvar categoria. Verifique os campos.")
                return JsonResponse({
                    "success": False,
                    "message": message,
                    "errors": form.errors
                }, status=400)
    else:
        form = CategoriaProdutoForm(instance=categoria)

    context = {"form": form, "categoria": categoria,}
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "partials/produtos/editar_categoria.html", context)

    return render(request, "base.html", {
        "content_template": "partials/produtos/editar_categoria.html",
        "data_page": "editar_categoria",
        **context,
    })

@require_POST
@login_required
def excluir_categorias_view(request):
    app_messages = get_app_messages(request)
    """
    Exclui múltiplas categorias de produto via AJAX.
    """
    if not request.headers.get("x-requested-with") == "XMLHttpRequest":
        message = app_messages.error("Requisição inválida.")
        return JsonResponse({"success": False, "message": message}, status=400)

    try:
        body = json.loads(request.body)
        ids = body.get("ids", [])
        if not ids:
            message = app_messages.error("Nenhuma categoria selecionada.")
            return JsonResponse({"success": False, "message": message}, status=400)

        count = len(ids)
        CategoriaProduto.objects.filter(id__in=ids).delete()
        message = app_messages.success_deleted("Categoria(s)", f"{count} selecionada(s)")
        return JsonResponse({"success": True, "message": message, "redirect_url": reverse("produto:lista_categorias")})
    except Exception as e:
        message = app_messages.error(f"Erro ao excluir categorias: {str(e)}")
        return JsonResponse({"success": False, "message": message}, status=500)

@login_required
def cadastrar_categoria_view(request):
    app_messages = get_app_messages(request)
    print("DEBUG: cadastrar_categoria_view acessada")
    if request.method == "POST":
        form = CategoriaProdutoForm(request.POST)
        print("DEBUG: Formulário de categoria válido:", form.is_valid())
        if form.is_valid():
            form.save()
            message = app_messages.success_created(form.instance)
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                print("DEBUG: Retornando JSON de sucesso para cadastro de categoria")
                return JsonResponse({
                    "success": True,
                    "message": message,
                    "redirect_url": reverse("produto:lista_categorias")
                })
            else:
                return redirect("produto:lista_categorias")
        else:
            # Tratamento de erro para AJAX
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                message = app_messages.error("Erro ao salvar categoria. Verifique os campos.")
                print("DEBUG: Retornando JSON de erro para cadastro de categoria")
                return JsonResponse({
                    "success": False,
                    "message": message,
                    "errors": form.errors
                }, status=400)

    else:
        form = CategoriaProdutoForm()

    return render_ajax_or_base(
        request,
        "partials/produtos/cadastrar_categoria.html",
        {"form": form, "data_tela": "cadastrar_categoria"}
    )

def categoria_list_api(request):
    """
    Retorna todas as categorias como JSON: [{id: <int>, nome: <str>}, ...]
    """
    qs = CategoriaProduto.objects.order_by('nome').values('id', 'nome')
    # safe=False porque estamos retornando uma lista, não um dict
    return JsonResponse(list(qs), safe=False)



# =====================
# UNIDADES
# =====================
@login_required
def lista_unidades_view(request):
    unidades = UnidadeMedida.objects.all()
    return render_ajax_or_base(request, "partials/produtos/lista_unidades.html", {"unidades": unidades})

@login_required
def cadastrar_unidade_view(request):
    app_messages = get_app_messages(request)
    if request.method == "POST":
        form = UnidadeMedidaForm(request.POST)
        if form.is_valid():
            form.save()
            app_messages.success_created(form.instance)
            return redirect(reverse("produto:lista_unidades"))
    else:
        form = UnidadeMedidaForm()
    return render_ajax_or_base(request, "partials/produtos/cadastrar_unidade.html", {"form": form})

@login_required
def editar_unidade_view(request, pk):
    app_messages = get_app_messages(request)
    print("DEBUG: editar_unidade_view accessed for PK:", pk)
    print("DEBUG: editar_unidade_view accessed for PK:", pk)
    print(f"DEBUG: editar_unidade_view - PK recebido: {pk}")
    unidade = get_object_or_404(UnidadeMedida, pk=pk)
    print(f"DEBUG: editar_unidade_view - Unidade encontrada: {unidade.sigla}")
    if request.method == "POST":
        form = UnidadeMedidaForm(request.POST, instance=unidade)
        if form.is_valid():
            form.save()
            message = app_messages.success_updated(unidade)
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": True, "message": message, "redirect_url": reverse("produto:lista_unidades")})
            else:
                return redirect(reverse("produto:lista_unidades"))
        else:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                message = app_messages.error("Erro ao atualizar unidade. Verifique os campos.")
                return JsonResponse({"success": False, "message": message, "errors": form.errors}, status=400)
            else:
                app_messages.error("Erro ao atualizar unidade. Verifique os campos.")
    else:
        form = UnidadeMedidaForm(instance=unidade)
    
    context = {"form": form, "unidade": unidade}
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "partials/produtos/editar_unidade.html", context)
    
    return render(request, "base.html", {
        "content_template": "partials/produtos/lista_unidades.html",
        **context,
    })

@require_POST
@login_required
def excluir_unidades_view(request):
    app_messages = get_app_messages(request)
    if not request.headers.get("x-requested-with") == "XMLHttpRequest":
        message = app_messages.error("Requisição inválida.")
        return JsonResponse({"success": False, "message": message}, status=400)

    try:
        data = json.loads(request.body.decode("utf-8"))
        ids = data.get("ids", [])
        if not ids:
            message = app_messages.error("Nenhuma unidade selecionada.")
            return JsonResponse({"success": False, "message": message}, status=400)

        count = len(ids)
        UnidadeMedida.objects.filter(id__in=ids).delete()
        message = app_messages.success_deleted("Unidade(s)", f"{count} selecionada(s)")
        return JsonResponse({"success": True, "message": message, "redirect_url": reverse("produto:lista_unidades")})

    except Exception as e:
        message = app_messages.error(f"Erro ao excluir: {str(e)}")
        return JsonResponse({"success": False, "message": message}, status=500)

def is_superuser_or_staff(user):
    return user.is_superuser or user.is_staff

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def manutencao_ncm_view(request):
    app_messages = get_app_messages(request)
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
def api_racoes_list(request):
    """
    Retorna uma lista de produtos da categoria 'Ração' em formato JSON.
    """
    racoes = Produto.objects.filter(categoria__nome__iexact='Ração').values('id', 'nome').order_by('nome')
    return JsonResponse(list(racoes), safe=False)


@login_required
@user_passes_test(is_superuser_or_staff)
def importar_ncm_manual_view(request):
    app_messages = get_app_messages(request)
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
        message = app_messages.success_imported(instance=None, custom_message=f"{count} códigos NCM importados com sucesso.")
        return JsonResponse({"success": True, "message": message})
    except Exception as e:
        message = app_messages.error(f"Erro ao importar NCM: {str(e)}")
        return JsonResponse({"success": False, "message": message}, status=500)
