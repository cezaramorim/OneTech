from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from common.messages_utils import get_app_messages
from .forms import EmpresaForm, CategoriaEmpresaForm
from .models import Empresa, CategoriaEmpresa
from django.contrib.auth.decorators import permission_required
from accounts.utils.decorators import login_required_json
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

@login_required_json
@permission_required('empresas.view_categoriaempresa', raise_exception=True)
def lista_categorias_view(request):
    categorias = CategoriaEmpresa.objects.all().order_by('nome')
    return render_ajax_or_base(request, 'partials/nova_empresa/lista_categorias.html', {
        'categorias': categorias
    })


@login_required_json
@permission_required('empresas.add_categoriaempresa', raise_exception=True)
def categoria_form_view(request, pk=None):
    app_messages = get_app_messages(request)
    if pk:
        categoria = get_object_or_404(CategoriaEmpresa, pk=pk)
    else:
        categoria = None
    
    form = CategoriaEmpresaForm(request.POST or None, instance=categoria)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            
            if pk:
                message = app_messages.success_updated(form.instance)
            else:
                message = app_messages.success_created(form.instance)

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'redirect_url': reverse('empresas:lista_categorias'), 'message': message})
            else:
                return redirect('empresas:lista_empresas_avancadas') # Redireciona para a lista de empresas
        else:
            # Formulário inválido
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors, 'message': app_messages.error('Erro ao salvar categoria. Verifique os campos.')}, status=400)
            else:
                app_messages.error('Erro ao salvar categoria. Verifique os campos.')

    context = {
        'form': form,
    }
    return render_ajax_or_base(request, 'partials/nova_empresa/categoria_form.html', context)


@require_POST
@login_required_json
@permission_required('empresas.delete_categoriaempresa', raise_exception=True)
def excluir_categorias_view(request):
    app_messages = get_app_messages(request)
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        if not ids:
            message = app_messages.error('Nenhum ID fornecido.')
            return JsonResponse({'success': False, 'message': message}, status=400)
        
        count = len(ids)
        CategoriaEmpresa.objects.filter(pk__in=ids).delete()
        
        message = app_messages.success_deleted("Categoria(s)", f"{count} selecionada(s)")
        return JsonResponse({'success': True, 'message': message, 'redirect_url': reverse('empresas:lista_categorias')})
    except json.JSONDecodeError:
        message = app_messages.error('Requisição inválida (JSON malformatado).')
        return JsonResponse({'success': False, 'message': message}, status=400)
    except Exception as e:
        message = app_messages.error(f'Erro ao excluir categorias: {str(e)}')
        return JsonResponse({'success': False, 'message': message}, status=500)


# === Nova Empresa (Unificada: Cadastro e Edição) ===
@login_required_json
@permission_required('empresas.add_empresaavancada', raise_exception=True)
def empresa_avancada_form_view(request, pk=None):
    app_messages = get_app_messages(request)
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
            if pk:
                message = app_messages.success_updated(form.instance)
            else:
                message = app_messages.success_created(form.instance)

            # Resposta para requisições AJAX
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'redirect_url': reverse('empresas:lista_empresas_avancadas')
                })
            
            # Redirecionamento padrão
            return redirect('empresas:lista_empresas_avancadas')
        else:
            # Em caso de formulário inválido, retorna os erros
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                message = app_messages.error('Erro ao salvar empresa. Verifique os campos.')
                return JsonResponse({'success': False, 'message': message, 'errors': form.errors}, status=400)
            else:
                app_messages.error('Erro ao salvar empresa. Verifique os campos.')

    context = {
        'form': form,
        'vendedores': get_user_model().objects.filter(groups__name__iexact='vendedores').order_by('first_name'),
        'estados': [
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
            'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
            'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        ],
        'empresa': empresa, # Passa a instância para o template
    }
    return render_ajax_or_base(request, 'partials/nova_empresa/cadastrar_empresa_avancada.html', context)



#from empresas.forms import EmpresaAvancadaFiltroForm  # Form opcional para organizar filtros

@login_required_json
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



@login_required_json
@csrf_exempt
@require_POST
def atualizar_status_empresa_avancada(request, pk):
    app_messages = get_app_messages(request)
    try:
        data = json.loads(request.body)
        empresa = EmpresaAvancada.objects.get(pk=pk)
        empresa.ativo = data.get('ativo', False)
        empresa.save()
        message = app_messages.success_updated(empresa, custom_message=f'Status da empresa "{empresa.razao_social or empresa.nome}" atualizado com sucesso.')
        return JsonResponse({'success': True, 'message': message})
    except Exception:
        message = app_messages.error('Erro ao atualizar o status da empresa.')
        return JsonResponse({'success': False, 'message': message}, status=500)


@require_POST
@login_required_json
@permission_required('empresas.delete_empresaavancada', raise_exception=True)
def excluir_empresas_avancadas_view(request):
    app_messages = get_app_messages(request)
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        if not ids:
            message = app_messages.error('Nenhum ID fornecido.')
            return JsonResponse({'success': False, 'message': message}, status=400)
        
        count = len(ids)
        EmpresaAvancada.objects.filter(pk__in=ids).delete()
        
        message = app_messages.success_deleted("Empresa(s)", f"{count} selecionada(s)")
        return JsonResponse({'success': True, 'message': message, 'redirect_url': reverse('empresas:lista_empresas_avancadas')})
    except json.JSONDecodeError:
        message = app_messages.error('Requisição inválida (JSON malformatado).')
        return JsonResponse({'success': False, 'message': message}, status=400)
    except Exception as e:
        message = app_messages.error(f'Erro ao excluir empresas: {str(e)}')
        return JsonResponse({'success': False, 'message': message}, status=500)


