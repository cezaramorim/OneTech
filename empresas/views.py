from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from .forms import EmpresaForm, CategoriaEmpresaForm
from .models import Empresa, CategoriaEmpresa
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from common.utils import render_ajax_or_base
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






# === Categorias ===

@login_required
@permission_required('empresas.view_categoriaempresa', raise_exception=True)
def lista_categorias_view(request):
    categorias = CategoriaEmpresa.objects.all().order_by('nome')
    return render(request, 'base.html', {
        'content_template': 'partials/nova_empresa/lista_categorias.html',
        'categorias': categorias
    })


@login_required
@permission_required('empresas.add_categoriaempresa', raise_exception=True)
def categoria_form_view(request, pk=None):
    if pk:
        categoria = get_object_or_404(CategoriaEmpresa, pk=pk)
    else:
        categoria = None
    
    form = CategoriaEmpresaForm(request.POST or None, instance=categoria)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f"Categoria {'atualizada' if pk else 'cadastrada'} com sucesso!")
        return JsonResponse({'redirect_url': reverse('empresas:lista_categorias')}) \
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' \
            else redirect('empresas:lista_categorias')

    context = {
        'form': form,
    }
    return render(request, 'base.html', {'content_template': 'partials/nova_empresa/categoria_form.html', **context})


@require_POST
@login_required
@permission_required('empresas.delete_categoriaempresa', raise_exception=True)
def excluir_categorias_view(request):
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        if not ids:
            return JsonResponse({'sucesso': False, 'erro': 'Nenhum ID fornecido.'}, status=400)
        
        CategoriaEmpresa.objects.filter(pk__in=ids).delete()
        
        messages.success(request, f"{len(ids)} categorias excluídas com sucesso.")
        return JsonResponse({'sucesso': True, 'redirect_url': reverse('empresas:lista_categorias')})
    except json.JSONDecodeError:
        return JsonResponse({'sucesso': False, 'erro': 'JSON inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'sucesso': False, 'erro': str(e)}, status=500)


# === Nova Empresa (Unificada: Cadastro e Edição) ===
@login_required
@permission_required('empresas.add_empresaavancada', raise_exception=True)
def empresa_avancada_form_view(request, pk=None):
    """
    View unificada para cadastrar e editar uma EmpresaAvancada.
    - Se `pk` for fornecido, edita a empresa existente.
    - Se `pk` for None, cria uma nova empresa.
    """
    if pk:
        empresa = get_object_or_404(EmpresaAvancada, pk=pk)
        # Garante que o usuário tem permissão para alterar esta empresa específica
        # (Implementar lógica de permissão de objeto se necessário)
    else:
        empresa = None

    # O formulário é instanciado com os dados da requisição (se houver) e a instância da empresa
    form = EmpresaAvancadaForm(request.POST or None, instance=empresa)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            
            # Mensagem de sucesso dinâmica
            mensagem_sucesso = f"Empresa '{form.instance.razao_social}' {'atualizada' if pk else 'cadastrada'} com sucesso!"
            messages.success(request, mensagem_sucesso)

            # Resposta para requisições AJAX
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'sucesso': True,
                    'redirect_url': reverse('empresas:lista_empresas_avancadas')
                })
            
            # Redirecionamento padrão
            return redirect('empresas:lista_empresas_avancadas')
        else:
            # Em caso de formulário inválido, retorna os erros
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': False, 'erros': form.errors}, status=400)

    # Contexto para o template
    vendedores = get_user_model().objects.filter(groups__name__iexact='vendedores').order_by('first_name')
    estados = [
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    ]
    
    # Converte a instância para um dicionário apenas se ela existir
    empresa_data = model_to_dict(empresa) if pk else None

    context = {
        'form': form,
        'today': now(),
        'vendedores': vendedores,
        'estados': estados,
        'empresa': empresa,  # Passa a instância para o template (útil para o título, etc.)
        'empresa_data': empresa_data, # Passa o dicionário para o json_script
        'titulo_pagina': f"Editar Empresa: {empresa.razao_social}" if pk else "Cadastrar Nova Empresa"
    }

    return render_ajax_or_base(request, 'partials/nova_empresa/cadastrar_empresa_avancada.html', context)



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
    status_map = {
        'ativo': 'ativa',
        'inativo': 'inativa',
    }
    if status in status_map:
        empresas = empresas.filter(status_empresa=status_map[status])
    

    

    return render_ajax_or_base(request, 'partials/nova_empresa/lista_empresas.html', {
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


@require_POST
@login_required
@permission_required('empresas.delete_empresaavancada', raise_exception=True)
def excluir_empresas_avancadas_view(request):
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        if not ids:
            return JsonResponse({'sucesso': False, 'erro': 'Nenhum ID fornecido.'}, status=400)
        
        EmpresaAvancada.objects.filter(pk__in=ids).delete()
        
        messages.success(request, f"{len(ids)} empresa(s) excluída(s) com sucesso.")
        return JsonResponse({'sucesso': True, 'redirect_url': reverse('empresas:lista_empresas_avancadas')})
    except json.JSONDecodeError:
        return JsonResponse({'sucesso': False, 'erro': 'JSON inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'sucesso': False, 'erro': str(e)}, status=500)


