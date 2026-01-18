# control/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.core.management import call_command
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test

from common.utils import render_ajax_or_base
from .models import Tenant
from .forms import TenantForm, TenantUserCreationForm, TenantUserChangeForm
from .utils import use_tenant
from accounts.models import User
from django.contrib.auth.models import Group

# --- Decorator para Superusuário ---
def superuser_required(view_func):
    """Decorator que garante que o usuário logado é um superusuário."""
    return user_passes_test(lambda u: u.is_superuser, login_url='/painel/')(view_func)

# --- Views de Gestão de Tenants (Clientes) ---

@superuser_required
def tenant_list_view(request):
    """Lista todos os tenants (clientes) cadastrados."""
    tenants = Tenant.objects.using('default').all().order_by('nome')
    context = {
        'tenants': tenants,
        'data_page': 'tenant_list',
    }
    return render_ajax_or_base(request, 'partials/control/tenant_list.html', context)

@superuser_required
def tenant_create_view(request):
    """Lida com a criação de um novo tenant."""
    if request.method == 'POST':
        form = TenantForm(request.POST, request.FILES, is_creation=True)
        if form.is_valid():
            try:
                opts = form.cleaned_data
                call_command(
                    'provisionar_tenant',
                    '--nome', opts['nome'],
                    '--slug', opts['slug'],
                    '--dominio', opts['dominio'],
                    '--razao_social', opts['razao_social'],
                    '--cnpj', opts['cnpj'],
                    '--admin-user', opts['admin_user'],
                    '--admin-email', opts['admin_email'],
                    '--admin-pass', opts['admin_pass'],
                )
                tenant = get_object_or_404(Tenant, slug=opts['slug'])
                form_for_save = TenantForm(request.POST, request.FILES, instance=tenant)
                if form_for_save.is_valid():
                    form_for_save.save()
                messages.success(request, f"Cliente '{opts['nome']}' provisionado com sucesso!")
                return redirect('control:tenant_list')
            except Exception as e:
                messages.error(request, f"Falha no provisionamento: {e}")
                # Limpeza: se o comando falhou, tenta apagar o registro do tenant que pode ter sido criado.
                Tenant.objects.filter(slug=opts.get('slug')).delete()
        else:
            messages.error(request, "Foram encontrados erros no formulário. Por favor, corrija-os.")
    else:
        form = TenantForm(is_creation=True)
    context = {'form': form, 'data_page': 'tenant_form'}
    return render_ajax_or_base(request, 'partials/control/tenant_form.html', context)

@superuser_required
def tenant_edit_view(request, pk):
    """Lida com a edição de um tenant existente."""
    tenant = get_object_or_404(Tenant, pk=pk)
    if request.method == 'POST':
        form = TenantForm(request.POST, request.FILES, instance=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, f"Cliente '{tenant.nome}' atualizado com sucesso!")
            return redirect('control:tenant_list')
    else:
        form = TenantForm(instance=tenant)
    context = {'form': form, 'tenant': tenant, 'data_page': 'tenant_form'}
    return render_ajax_or_base(request, 'partials/control/tenant_form.html', context)

# --- Views de Gestão de Usuários por Tenant ---

@superuser_required
def tenant_user_list_view(request):
    """
    Página principal para listar usuários de um tenant selecionado.
    Carrega o primeiro tenant por padrão se nenhum for especificado.
    Responde a requisições AJAX para atualizar a lista de usuários.
    """
    if not request.user.is_superuser:
        return HttpResponseForbidden("Acesso negado.")

    tenants = Tenant.objects.using('default').filter(ativo=True).order_by('nome')
    selected_tenant_id = request.GET.get('tenant_id')
    
    users = None
    selected_tenant = None

    if selected_tenant_id:
        selected_tenant = get_object_or_404(Tenant, pk=selected_tenant_id)
    elif tenants.exists():
        # Se nenhum tenant for selecionado na URL, seleciona o primeiro da lista como padrão.
        selected_tenant = tenants.first()

    # Se temos um tenant (selecionado ou o padrão), busca seus usuários.
    if selected_tenant:
        with use_tenant(selected_tenant):
            users = User.objects.all().order_by('nome_completo')

    # Se a requisição for AJAX, retorna apenas o HTML da tabela de usuários.
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        context = {
            'selected_tenant': selected_tenant,
            'users': users,
        }
        return render(request, 'partials/control/_tenant_user_table.html', context)

    # Para a carga inicial da página, renderiza o layout completo.
    context = {
        'tenants': tenants,
        'selected_tenant': selected_tenant,
        'users': users,
        'data_page': 'tenant_user_list',
    }
    return render_ajax_or_base(request, 'partials/control/tenant_user_list.html', context)

@superuser_required
def tenant_user_create_view(request, tenant_id):
    """Cria um novo usuário dentro do contexto de um tenant específico."""
    tenant = get_object_or_404(Tenant, pk=tenant_id)
    with use_tenant(tenant):
        if request.method == 'POST':
            form = TenantUserCreationForm(request.POST)
            form.fields['grupo'].queryset = Group.objects.all()
            if form.is_valid():
                form.save()
                messages.success(request, f"Usuário '{form.cleaned_data['username']}' criado com sucesso para o cliente {tenant.nome}.")
                return redirect(f"{reverse('control:tenant_user_list')}?tenant_id={tenant.id}")
        else:
            form = TenantUserCreationForm()
            form.fields['grupo'].queryset = Group.objects.all()
    context = {'form': form, 'tenant': tenant, 'data_page': 'tenant_user_form'}
    return render_ajax_or_base(request, 'partials/control/tenant_user_form.html', context)

@superuser_required
def tenant_user_edit_view(request, tenant_id, user_id):
    """Edita um usuário existente dentro do contexto de um tenant."""
    tenant = get_object_or_404(Tenant, pk=tenant_id)
    with use_tenant(tenant):
        user_to_edit = get_object_or_404(User, pk=user_id)
        if request.method == 'POST':
            form = TenantUserChangeForm(request.POST, instance=user_to_edit)
            form.fields['grupo'].queryset = Group.objects.all()
            if form.is_valid():
                form.save()
                messages.success(request, f"Usuário '{user_to_edit.username}' atualizado com sucesso.")
                return redirect(f"{reverse('control:tenant_user_list')}?tenant_id={tenant.id}")
        else:
            form = TenantUserChangeForm(instance=user_to_edit)
            form.fields['grupo'].queryset = Group.objects.all()
            if user_to_edit.groups.exists():
                form.fields['grupo'].initial = user_to_edit.groups.first()
    context = {'form': form, 'tenant': tenant, 'user_to_edit': user_to_edit, 'data_page': 'tenant_user_form'}
    return render_ajax_or_base(request, 'partials/control/tenant_user_form.html', context)

@superuser_required
@require_POST
def tenant_user_toggle_active_view(request, tenant_id, user_id):
    """Ativa ou desativa um usuário via AJAX."""
    tenant = get_object_or_404(Tenant, pk=tenant_id)
    with use_tenant(tenant):
        try:
            user = User.objects.get(pk=user_id)
            user.is_active = not user.is_active
            user.save()
            return JsonResponse({'success': True, 'is_active': user.is_active})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Usuário não encontrado.'}, status=404)
    return JsonResponse({'success': False, 'message': 'Ocorreu um erro inesperado.'}, status=500)

def ping_view(request):
    return HttpResponse("Pong! A URL de controle está funcionando.")


# ==============================================================================
# 🚀 VIEWS PARA EMITENTE (MATRIZ/FILIAIS)
# ==============================================================================
from .models import Emitente
from .forms import EmitenteForm

@login_required
# @permission_required('control.view_emitente', raise_exception=True)
def lista_emitentes(request):
    """
    Lista todos os emitentes cadastrados no banco de dados atual.
    """
    emitentes = Emitente.objects.all().order_by('-is_default', 'nome_fantasia')
    context = {'emitentes': emitentes}
    return render_ajax_or_base(request, 'partials/control/lista_emitentes.html', context)

@login_required
# @permission_required('control.add_emitente', raise_exception=True)
def criar_emitente(request):
    """
    Cria um novo emitente.
    """
    if request.method == 'POST':
        form = EmitenteForm(request.POST, request.FILES)
        if form.is_valid():
            emitente = form.save()
            messages.success(request, f'Emitente "{emitente.nome_fantasia or emitente.razao_social}" criado com sucesso!')
            return JsonResponse({'success': True, 'redirect_url': reverse('control:lista_emitentes')})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = EmitenteForm()
    
    context = {'form': form}
    return render_ajax_or_base(request, 'partials/control/form_emitente.html', context)

@login_required
# @permission_required('control.change_emitente', raise_exception=True)
def editar_emitente(request, pk):
    """
    Edita um emitente existente.
    """
    emitente = get_object_or_404(Emitente, pk=pk)
    if request.method == 'POST':
        form = EmitenteForm(request.POST, request.FILES, instance=emitente)
        if form.is_valid():
            form.save()
            messages.success(request, f'Emitente "{emitente.nome_fantasia or emitente.razao_social}" atualizado com sucesso!')
            return JsonResponse({'success': True, 'redirect_url': reverse('control:lista_emitentes')})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = EmitenteForm(instance=emitente)

    context = {'form': form, 'emitente': emitente}
    return render_ajax_or_base(request, 'partials/control/form_emitente.html', context)

@login_required
@require_POST
# @permission_required('control.delete_emitente', raise_exception=True)
def excluir_emitente(request, pk):
    """
    Exclui um emitente.
    """
    emitente = get_object_or_404(Emitente, pk=pk)
    nome_emitente = emitente.nome_fantasia or emitente.razao_social
    emitente.delete()
    messages.success(request, f'Emitente "{nome_emitente}" excluído com sucesso.')
    # A resposta JSON é para o caso de o frontend tratar a exclusão via fetch/AJAX
    return JsonResponse({'success': True, 'redirect_url': reverse('control:lista_emitentes')})
