from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from .forms import EmpresaForm, CategoriaEmpresaForm
from .models import Empresa, CategoriaEmpresa
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from accounts.utils.render import render_ajax_or_base
from django.urls import reverse

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

@login_required
@permission_required('empresas.add_categoriaempresa', raise_exception=True)
def cadastrar_categoria_avancada(request):
    form = CategoriaEmpresaForm(request.POST or None)
    categorias = CategoriaEmpresa.objects.all().order_by('-id')  # ✅ Importante!

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Categoria cadastrada com sucesso!")
        return JsonResponse({'redirect_url': reverse('empresas:cadastrar_categoria_avancada')}) \
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' \
            else redirect('empresas:cadastrar_categoria_avancada')

    return render_ajax_or_base(request, 'partials/nova_empresa/cadastrar_categoria.html', {
        'form': form,
        'categorias': categorias,  # ✅ Fundamental!
    })




# === Nova Empresa ===
@login_required
@permission_required('empresas.add_empresa', raise_exception=True)
def cadastrar_empresa_avancado(request):
    from .forms import EmpresaAvancadaForm  # 📌 Novo formulário
    from .models import EmpresaAvancada     # 📌 Novo model

    # Lista de vendedores para o campo select
    vendedores = get_user_model().objects.filter(groups__name__iexact='vendedores').order_by('first_name')

    # Lista de estados brasileira (mantida)
    estados = [
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    ]

    # Instanciando o formulário
    form = EmpresaAvancadaForm(request.POST or None)

    # Se for POST e formulário for válido, salvar
    if request.method == 'POST' and form.is_valid():
        form.save()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'redirect_url': '/empresas/lista/'})
        messages.success(request, "Empresa cadastrada com sucesso!")
        return redirect('empresas:lista_empresas')

    # Renderização via AJAX ou base
    return render_ajax_or_base(request, 'partials/nova_empresa/cadastrar_empresa_avancado.html', {
        'form': form,
        'today': now(),
        'vendedores': vendedores,
        'estados': estados,
    })
