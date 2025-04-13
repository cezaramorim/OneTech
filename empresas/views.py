from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from .forms import EmpresaForm, CategoriaEmpresaForm
from .models import Empresa, CategoriaEmpresa


# === Função auxiliar ===

def render_ajax_or_base(request, partial_template, context=None):
    context = context or {}
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, partial_template, context)
    return render(request, 'base.html', {'content_template': partial_template, **context})


# === Empresas ===

def cadastrar_empresa(request):
    form = EmpresaForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'redirect_url': '/empresas/lista/'})
        return redirect('empresas:lista_empresas')

    return render_ajax_or_base(request, 'partials/empresas/cadastrar_empresa.html', {
        'form': form
    })


def lista_empresas(request):
    empresas = Empresa.objects.all()
    return render_ajax_or_base(request, 'partials/empresas/lista_empresas.html', {
        'empresas': empresas
    })


def editar_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    form = EmpresaForm(request.POST or None, instance=empresa)

    if request.method == 'POST' and form.is_valid():
        form.save()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'redirect_url': '/empresas/lista/'})
        return redirect('empresas:lista_empresas')

    return render_ajax_or_base(request, 'partials/empresas/editar_empresa.html', {
        'form': form,
        'empresa': empresa
    })


def excluir_empresa_multiplo(request):
    """
    Exclui múltiplas empresas a partir de uma lista de IDs.
    Retorna resposta AJAX ou redireciona.
    """
    ids = request.POST.getlist('empresas_selecionadas')

    if not ids:
        msg = "Nenhuma empresa selecionada para exclusão."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': msg}, status=400)
        messages.warning(request, msg)
        return redirect('empresas:lista_empresas')

    empresas = Empresa.objects.filter(id__in=ids)
    nomes = [e.nome_empresa for e in empresas]
    empresas.delete()

    msg = f"{len(nomes)} empresa(s) excluída(s): {', '.join(nomes)}."
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': msg})
    messages.success(request, msg)
    return redirect('empresas:lista_empresas')


# === Categorias ===

def cadastrar_categoria(request):
    form = CategoriaEmpresaForm(request.POST or None)
    categorias = CategoriaEmpresa.objects.all()

    if request.method == 'POST' and form.is_valid():
        form.save()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'redirect_url': '/empresas/categoria/cadastrar/'})
        return redirect('empresas:cadastrar_categoria')

    return render_ajax_or_base(request, 'partials/empresas/cadastrar_categoria.html', {
        'form': form,
        'categorias': categorias
    })

