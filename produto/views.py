import json

import requests
from django.db.models import Count, Q, Value
from django.db.models.functions import Replace
from django.contrib import messages
from common.messages_utils import get_app_messages
from django.urls import reverse
from django.forms import inlineformset_factory
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from accounts.utils.decorators import login_required_json
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from .forms import ProdutoForm, CategoriaProdutoForm, UnidadeMedidaForm, DetalhesFiscaisProdutoForm
from .models import Produto, CategoriaProduto, UnidadeMedida, NCM, DetalhesFiscaisProduto
from common.utils import render_ajax_or_base
from .ncm_services import consolidate_ncm_duplicates, import_ncm_from_local_json, inspect_ncm_duplicates, load_ncm_json, normalize_external_ncm_payload, save_ncm_json
from .ncm_utils import carregar_metadados_ncm, formatar_codigo_ncm, normalizar_codigo_ncm, normalizar_texto_mojibake, obter_nivel_ncm

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
@login_required_json
def lista_produtos_view(request):
    produtos = Produto.objects.all()
    return render_ajax_or_base(request, "partials/produtos/lista_produtos.html", {"produtos": produtos})


@login_required_json
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

@login_required_json
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
            print("FormulÃ¡rio de Produto Ã© vÃ¡lido.")
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
            print("Formulario de Produto NAO e valido.")
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

    # Se nÃ£o for AJAX, renderiza com base.html e content_template
    context["content_template"] = "partials/produtos/editar_produto.html"
    context["data_page"] = "editar_produto"
    return render(request, "base.html", context)


@require_POST
@login_required_json
def excluir_produtos_multiplos_view(request):
    app_messages = get_app_messages(request)
    if not request.headers.get("x-requested-with") == "XMLHttpRequest":
        message = app_messages.error("RequisiÃ§Ã£o invÃ¡lida.")
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
@login_required_json
def lista_categorias_view(request):
    categorias = CategoriaProduto.objects.all()
    return render_ajax_or_base(
        request,
        "partials/produtos/lista_categorias.html",
        {
            "categorias": categorias,
            "data_tela": "lista_categorias",  # âœ… Adicionado aqui
            "data_page": "lista_categorias",
        }
    )
    
@login_required_json
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
@login_required_json
def excluir_categorias_view(request):
    app_messages = get_app_messages(request)
    """
    Exclui mÃºltiplas categorias de produto via AJAX.
    """
    if not request.headers.get("x-requested-with") == "XMLHttpRequest":
        message = app_messages.error("RequisiÃ§Ã£o invÃ¡lida.")
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

@login_required_json
def cadastrar_categoria_view(request):
    app_messages = get_app_messages(request)
    print("DEBUG: cadastrar_categoria_view acessada")
    if request.method == "POST":
        form = CategoriaProdutoForm(request.POST)
        print("DEBUG: FormulÃ¡rio de categoria vÃ¡lido:", form.is_valid())
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
    # safe=False porque estamos retornando uma lista, nÃ£o um dict
    return JsonResponse(list(qs), safe=False)



# =====================
# UNIDADES
# =====================
@login_required_json
def lista_unidades_view(request):
    unidades = UnidadeMedida.objects.all()
    return render_ajax_or_base(request, "partials/produtos/lista_unidades.html", {"unidades": unidades})

@login_required_json
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

@login_required_json
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
@login_required_json
def excluir_unidades_view(request):
    app_messages = get_app_messages(request)
    if not request.headers.get("x-requested-with") == "XMLHttpRequest":
        message = app_messages.error("RequisiÃ§Ã£o invÃ¡lida.")
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


def _build_ncm_search_query(termo):
    termo = (termo or '').strip()
    if not termo:
        return Q()

    codigo_busca = normalizar_codigo_ncm(termo)
    descricao_query = Q(descricao__icontains=termo)

    # Para codigos, a busca deve respeitar a hierarquia do NCM.
    if codigo_busca and codigo_busca == ''.join(ch for ch in termo if ch.isdigit()):
        return (
            Q(codigo_sem_pontuacao__startswith=codigo_busca)
            | Q(codigo__startswith=termo)
            | descricao_query
        )

    return (
        Q(codigo_sem_pontuacao__icontains=codigo_busca)
        | Q(codigo__icontains=termo)
        | descricao_query
    )

@login_required_json
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def manutencao_ncm_view(request):
    termo = request.GET.get("term", "").strip()
    partial_only = request.GET.get("partial") == "1"
    ncm_lista = NCM.objects.annotate(
        produtos_vinculados=Count("detalhesfiscaisproduto", distinct=True),
        codigo_sem_pontuacao=Replace("codigo", Value("."), Value("")),
    )

    if termo:
        ncm_lista = ncm_lista.filter(
            _build_ncm_search_query(termo)
        ).order_by("codigo")[:50]
    else:
        ncm_lista = ncm_lista.order_by("codigo")[:500]

    ncm_lista = list(ncm_lista)
    for item in ncm_lista:
        item.nivel = obter_nivel_ncm(item.codigo)

    context = {
        "ncm_lista": ncm_lista,
        "ncm_meta": carregar_metadados_ncm(),
    }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        if partial_only:
            return render(request, "partials/produtos/tabela_ncm.html", context)
        return render(request, "partials/produtos/manutencao_ncm.html", context)

    return render(request, "base.html", {
        "content_template": "partials/produtos/manutencao_ncm.html",
        **context,
    })


@login_required_json
def buscar_ncm_ajax(request):
    termo = (request.GET.get('term', '') or request.GET.get('search', '')).strip()
    resultados = []

    if termo:
        qs = NCM.objects.annotate(
            codigo_sem_pontuacao=Replace("codigo", Value("."), Value(""))
        ).filter(
            _build_ncm_search_query(termo)
        ).order_by('codigo')[:20]
        resultados = [
            {
                "id": ncm.codigo,
                "codigo": ncm.codigo,
                "codigo_formatado": ncm.codigo_formatado,
                "descricao": ncm.descricao,
                "nivel": obter_nivel_ncm(ncm.codigo),
                "text": f"{ncm.codigo_formatado} - {ncm.descricao}",
            }
            for ncm in qs
        ]

    return JsonResponse({"results": resultados})

@login_required_json
def api_racoes_list(request):
    """
    Retorna uma lista de produtos da categoria 'Ração' em formato JSON.
    """
    racoes = Produto.objects.filter(categoria__nome__iexact='Ração').values('id', 'nome').order_by('nome')
    return JsonResponse(list(racoes), safe=False)


@login_required_json
@user_passes_test(is_superuser_or_staff)
@require_POST
def atualizar_ncm_base_oficial_view(request):
    app_messages = get_app_messages(request)
    try:
        try:
            existing_metadata = load_ncm_json()
        except FileNotFoundError:
            existing_metadata = {}

        url = 'https://portalunico.siscomex.gov.br/classif/api/publico/nomenclatura/download/json'
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        normalized_data = normalize_external_ncm_payload(response.json(), existing_metadata)
        save_ncm_json(normalized_data)

        total_itens = len(normalized_data.get('Nomenclaturas', []))
        message = app_messages.success_process(f'Base oficial NCM atualizada com sucesso. {total_itens} itens salvos no arquivo local.')
        return JsonResponse({
            'success': True,
            'message': message,
            'metadata': {
                'vigencia': normalized_data.get('Data_Ultima_Atualizacao_NCM', ''),
                'ato': normalized_data.get('Ato', ''),
                'total_itens': total_itens,
            }
        })
    except Exception as e:
        message = app_messages.error(f'Erro ao atualizar a base oficial de NCM: {str(e)}')
        return JsonResponse({'success': False, 'message': message}, status=500)


@login_required_json
@user_passes_test(is_superuser_or_staff)
@require_POST
def importar_ncm_local_view(request):
    app_messages = get_app_messages(request)
    try:
        result = import_ncm_from_local_json()
        duplicate_summary = inspect_ncm_duplicates()
        message = app_messages.success_process(
            f"{result['count']} codigos NCM importados/atualizados a partir da base local."
        )
        return JsonResponse({
            'success': True,
            'message': message,
            'metadata': result['metadata'],
            'import_count': result['count'],
            'duplicate_summary': duplicate_summary,
        })
    except FileNotFoundError:
        message = app_messages.error('Arquivo ncm.json nao encontrado em produto/data/.')
        return JsonResponse({'success': False, 'message': message}, status=404)
    except Exception as e:
        message = app_messages.error(f'Erro ao importar a base local de NCM: {str(e)}')
        return JsonResponse({'success': False, 'message': message}, status=500)


@login_required_json
@user_passes_test(is_superuser_or_staff)
@require_POST
def consolidar_ncm_view(request):
    app_messages = get_app_messages(request)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}') if request.body else {}
        apply_changes = bool(payload.get('apply'))
        duplicate_summary = consolidate_ncm_duplicates() if apply_changes else inspect_ncm_duplicates()

        if duplicate_summary['group_count'] == 0:
            message = app_messages.success_process('Nenhuma duplicidade de NCM encontrada.')
        elif apply_changes:
            message = app_messages.success_process(
                f"Consolidacao concluida. {duplicate_summary['group_count']} grupo(s) tratados."
            )
        else:
            message = app_messages.warning(
                f"{duplicate_summary['group_count']} grupo(s) de NCM com duplicidade encontrado(s)."
            )

        return JsonResponse({
            'success': True,
            'message': message,
            'applied': apply_changes,
            'duplicate_summary': duplicate_summary,
        })
    except json.JSONDecodeError:
        message = app_messages.error('Payload invalido para consolidacao de NCM.')
        return JsonResponse({'success': False, 'message': message}, status=400)
    except Exception as e:
        message = app_messages.error(f'Erro ao consolidar NCM: {str(e)}')
        return JsonResponse({'success': False, 'message': message}, status=500)


@login_required_json
@user_passes_test(is_superuser_or_staff)
@require_POST
def importar_ncm_manual_view(request):
    return atualizar_ncm_base_oficial_view(request)


