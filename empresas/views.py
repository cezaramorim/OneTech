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
from django.http import HttpResponse, HttpResponseBadRequest
from django.template.loader import render_to_string
from django.forms.models import model_to_dict
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from empresas.forms import EmpresaAvancadaForm

from django.shortcuts import render
from empresas.models import EmpresaAvancada

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from empresas.models import EmpresaAvancada

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q
from .models import EmpresaAvancada



# === Função auxiliar ===

def render_ajax_or_base(request, partial_template, context=None):
    context = context or {}
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, partial_template, context)
    return render(request, 'base.html', {'content_template': partial_template, **context})


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
from django.forms.models import model_to_dict

@login_required
@permission_required('empresas.add_empresa', raise_exception=True)
def cadastrar_empresa_avancada(request):
    from .forms import EmpresaAvancadaForm
    from .models import EmpresaAvancada

    vendedores = get_user_model().objects.filter(groups__name__iexact='vendedores').order_by('first_name')

    estados = [
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    ]

    form = EmpresaAvancadaForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'sucesso': True,
                    'redirect_url': reverse('empresas:cadastrar_empresa_avancado')
                })
            messages.success(request, "Empresa cadastrada com sucesso!")
            return redirect('empresas:cadastrar_empresa_avancada')

        # ❌ Form inválido — Retorna erros
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'sucesso': False,
                'erros': form.errors
            }, status=400)

    return render_ajax_or_base(request, 'partials/nova_empresa/cadastrar_empresa_avancada.html', {
        'form': form,
        'today': now(),
        'vendedores': vendedores,
        'estados': estados,
    })


#from empresas.forms import EmpresaAvancadaFiltroForm  # Form opcional para organizar filtros

@login_required
def lista_empresas_avancadas_view(request):
    """
    View que lista empresas avançadas com suporte a:
    - filtro unificado por termo (razão social ou CNPJ)
    - filtro por tipo de empresa (PF ou PJ)
    - filtro por status (ativa/inativa)
    - compatível com AJAX e base.html
    """

    empresas = EmpresaAvancada.objects.select_related('categoria').all()

    # 🔍 Parâmetros de busca
    termo = request.GET.get('termo_empresa', '').strip()
    tipo = request.GET.get('tipo', '').strip()      # Esperado: 'PJ' ou 'PF'
    status = request.GET.get('status', '').strip()  # Esperado: 'ativo' ou 'inativo'

    # 🔎 Filtro por termo (razão social ou CNPJ)
    if termo:
        empresas = empresas.filter(
            Q(razao_social__icontains=termo) |
            Q(cnpj__icontains=termo) |
            Q(nome__icontains=termo) |
            Q(nome_fantasia__icontains=termo)
        )

    # 🔎 Filtro por tipo de empresa (PF/PJ)
    if tipo == "PJ":
        empresas = empresas.filter(tipo_empresa="PJ")
    elif tipo == "PF":
        empresas = empresas.filter(tipo_empresa="PF")

    # 🔎 Filtro por status (ativo ou inativo)
    if status == 'ativa':
        empresas = empresas.filter(status_empresa=True)
    elif status == 'inativa':
        empresas = empresas.filter(status_empresa=False)

    return render(request, 'base.html', {
        'content_template': 'partials/nova_empresa/lista_empresas.html',
        'empresas': empresas,
        'request': request
    })



@csrf_exempt
@require_POST
def atualizar_status_empresa_avancada(request, pk):
    try:
        data = json.loads(request.body)
        empresa = EmpresaAvancada.objects.get(pk=pk)
        empresa.ativo = data.get('ativo', False)
        empresa.save()
        return JsonResponse({'sucesso': True, 'mensagem': 'Status atualizado com sucesso.'})
    except Exception:
        return JsonResponse({'sucesso': False, 'mensagem': 'Erro ao atualizar o status.'})

@login_required
def editar_empresa_avancada_view(request, pk):
    empresa = get_object_or_404(EmpresaAvancada, pk=pk)

    if request.method == 'POST':
        form = EmpresaAvancadaForm(request.POST, instance=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empresa atualizada com sucesso.')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': True, 'redirect_url': reverse('empresas:lista_empresas')})
            return redirect('empresas:lista_empresas')
    else:
        form = EmpresaAvancadaForm(instance=empresa)

    template = 'partials/nova_empresa/cadastrar_empresa_avancada.html'
    context = {'form': form, 'empresa': empresa}

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, template, context)

    return render(request, 'base.html', {'content_template': template, **context})
