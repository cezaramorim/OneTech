# control/views.py
from io import StringIO
from django.shortcuts import render, redirect, get_object_or_404
from django.core.management import call_command
from django.db import connections, DEFAULT_DB_ALIAS
from django.db.migrations.loader import MigrationLoader
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.apps import apps as django_apps
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.conf import settings

from common.utils import render_ajax_or_base
from .models import Tenant
from .forms import TenantForm, TenantUserCreationForm, TenantUserChangeForm
from .utils import is_principal_context, use_tenant
from control.db_router import TenantRouter
from accounts.models import User
from django.contrib.auth.models import Group

# --- Decorator para Superusuário ---
def superuser_required(view_func):
    """Decorator que garante que o usuário logado é um superusuário."""
    return user_passes_test(lambda u: u.is_superuser, login_url='/painel/')(view_func)

def principal_context_required(view_func):
    """Bloqueia acessos que devem existir apenas no contexto principal do software."""
    def _wrapped(request, *args, **kwargs):
        if not is_principal_context(request):
            messages.error(request, 'Area restrita. Entre em contato com o suporte tecnico.')
            return redirect('painel:home')
        return view_func(request, *args, **kwargs)
    return _wrapped

def _configure_database_alias(alias, db_settings):
    connections.databases[alias] = db_settings
    if alias in connections:
        connections[alias].close()
        connections[alias].settings_dict = db_settings


def _build_tenant_db_settings(tenant):
    cfg = connections[DEFAULT_DB_ALIAS].settings_dict.copy()
    cfg.update({
        'NAME': tenant.db_name,
        'USER': tenant.db_user,
        'PASSWORD': tenant.db_password,
        'HOST': tenant.db_host,
        'PORT': tenant.db_port,
    })
    return cfg


def _summarize_tenant_status(status_by_target, tenants, app_rows):
    summary = {}
    for app in app_rows:
        label = app['label']
        if not app['runs_on_tenants']:
            summary[label] = {'state': 'na', 'ok': 0, 'pending': 0, 'error': 0, 'total': 0, 'title': 'Nao se aplica aos tenants'}
            continue

        counts = {'ok': 0, 'pending': 0, 'error': 0, 'na': 0}
        for tenant in tenants:
            cell = status_by_target.get(tenant.slug, {}).get(label, {'state': 'error', 'title': 'Status indisponivel'})
            counts[cell['state']] = counts.get(cell['state'], 0) + 1

        total = len(tenants)
        if counts['error']:
            state = 'error'
            title = f"{counts['error']} tenant(s) com erro"
        elif counts['pending']:
            state = 'pending'
            title = f"{counts['pending']} tenant(s) com pendencia"
        else:
            state = 'ok'
            title = 'Todos os tenants estao em dia'

        summary[label] = {
            'state': state,
            'ok': counts['ok'],
            'pending': counts['pending'],
            'error': counts['error'],
            'total': total,
            'title': title,
        }

    return summary


def _collect_migration_status(tenants, app_rows):
    status_by_target = {}
    app_labels = [row['label'] for row in app_rows]

    def summarize(alias, applicable_labels):
        loader = MigrationLoader(connections[alias], ignore_no_migrations=True)
        applied = loader.applied_migrations
        disk = loader.disk_migrations
        result = {}
        for label in app_labels:
            if label not in applicable_labels:
                result[label] = {'state': 'na', 'pending_count': 0, 'title': 'Nao se aplica'}
                continue
            disk_keys = [key for key in disk if key[0] == label]
            pending = [key for key in disk_keys if key not in applied]
            if pending:
                result[label] = {
                    'state': 'pending',
                    'pending_count': len(pending),
                    'title': f'{len(pending)} migracao(oes) pendente(s)',
                }
            else:
                result[label] = {
                    'state': 'ok',
                    'pending_count': 0,
                    'title': 'Sem migracoes pendentes',
                }
        return result

    default_labels = {row['label'] for row in app_rows if row['runs_on_default']}
    try:
        status_by_target['default'] = summarize(DEFAULT_DB_ALIAS, default_labels)
    except Exception as exc:
        status_by_target['default'] = {label: {'state': 'error', 'pending_count': 0, 'title': str(exc)} for label in app_labels}

    tenant_labels = {row['label'] for row in app_rows if row['runs_on_tenants']}
    for tenant in tenants:
        alias = f"tenant_status_{tenant.id}"
        try:
            _configure_database_alias(alias, _build_tenant_db_settings(tenant))
            status_by_target[tenant.slug] = summarize(alias, tenant_labels)
        except Exception as exc:
            status_by_target[tenant.slug] = {label: {'state': 'error', 'pending_count': 0, 'title': str(exc)} for label in app_labels}
        finally:
            if alias in connections:
                connections[alias].close()
            if alias in connections.databases:
                del connections.databases[alias]

    return status_by_target


def _get_apps_migration_scope():
    router = TenantRouter()
    visible_core_labels = {'admin', 'auth', 'contenttypes', 'sessions'}
    hidden_labels = {'rest_framework', 'django_filters', 'widget_tweaks', 'django_extensions', 'humanize', 'staticfiles', 'messages'}
    app_rows = []

    for config in django_apps.get_app_configs():
        label = config.label
        if label in hidden_labels:
            continue

        is_local_app = str(config.path).startswith(str(settings.BASE_DIR))
        if not is_local_app and label not in visible_core_labels:
            continue

        app_rows.append({
            'label': label,
            'name': str(config.verbose_name).title() if config.verbose_name else label.title(),
            'runs_on_default': router.allow_migrate('default', label),
            'runs_on_tenants': router.allow_migrate('tenant', label),
        })

    return sorted(app_rows, key=lambda item: item['label'])


def _get_pending_tenant_slugs(status_by_target, tenants, app_rows):
    tenant_app_labels = [row['label'] for row in app_rows if row['runs_on_tenants']]
    pending_slugs = []

    for tenant in tenants:
        tenant_status = status_by_target.get(tenant.slug, {})
        has_pending = any(tenant_status.get(label, {}).get('state') == 'pending' for label in tenant_app_labels)
        if has_pending:
            pending_slugs.append(tenant.slug)

    return pending_slugs


@superuser_required
@principal_context_required
def central_migracoes_view(request):
    tenants = list(Tenant.objects.using('default').filter(ativo=True).order_by('nome'))
    selected_tenant_slugs = request.GET.getlist('tenant_view')
    only_pending_tenants = request.GET.get('only_pending') == '1'

    if request.method == 'POST':
        run_default = request.POST.get('executar_default') == 'on'
        run_tenants = request.POST.get('executar_tenants') == 'on'
        run_all_tenants = request.POST.get('todos_tenants') == 'on'
        fake = request.POST.get('modo_fake') == 'on'
        tenant_slugs = request.POST.getlist('tenants')

        if not run_default and not run_tenants:
            return JsonResponse({'success': False, 'message': 'Selecione ao menos um destino de migracao.'}, status=400)

        if run_tenants and not run_all_tenants and not tenant_slugs:
            return JsonResponse({'success': False, 'message': 'Selecione ao menos um tenant ou marque Todos os tenants.'}, status=400)

        try:
            executed_targets = []

            if run_default:
                output_default = StringIO()
                call_command('migrate', interactive=False, fake=fake, stdout=output_default, stderr=output_default)
                executed_targets.append('default')

            if run_tenants:
                output_tenants = StringIO()
                tenant_kwargs = {'fake': fake, 'stdout': output_tenants, 'stderr': output_tenants}
                if run_all_tenants:
                    tenant_kwargs['all'] = True
                else:
                    tenant_kwargs['tenants'] = tenant_slugs
                call_command('migrate_tenants', **tenant_kwargs)
                executed_targets.append('tenants')
        except Exception as exc:
            return JsonResponse({'success': False, 'message': f'Falha ao executar migracoes: {exc}'}, status=500)

        modo = ' em modo fake' if fake else ''
        destinos = ' e '.join(executed_targets)
        return JsonResponse({
            'success': True,
            'message': f'Migracoes executadas com sucesso em {destinos}{modo}.',
            'redirect_url': reverse('control:central_migracoes'),
        })

    apps_migration_scope = _get_apps_migration_scope()
    migration_status_by_target = _collect_migration_status(tenants, apps_migration_scope)
    tenant_status_summary = _summarize_tenant_status(migration_status_by_target, tenants, apps_migration_scope)
    pending_tenant_slugs = _get_pending_tenant_slugs(migration_status_by_target, tenants, apps_migration_scope)

    base_visible_slugs = selected_tenant_slugs or pending_tenant_slugs if only_pending_tenants else selected_tenant_slugs
    if only_pending_tenants and selected_tenant_slugs:
        base_visible_slugs = [slug for slug in selected_tenant_slugs if slug in pending_tenant_slugs]

    visible_tenants = [tenant for tenant in tenants if tenant.slug in base_visible_slugs] if base_visible_slugs else []

    context = {
        'apps_migration_scope': apps_migration_scope,
        'migration_status_by_target': migration_status_by_target,
        'tenant_status_summary': tenant_status_summary,
        'tenants': tenants,
        'visible_tenants': visible_tenants,
        'selected_tenant_slugs': selected_tenant_slugs,
        'only_pending_tenants': only_pending_tenants,
        'pending_tenant_slugs': pending_tenant_slugs,
        'data_page': 'central_migracoes',
    }
    return render_ajax_or_base(request, 'partials/control/central_migracoes.html', context)


# --- Views de Gestão de Tenants (Clientes) ---

@superuser_required
@principal_context_required
def tenant_list_view(request):
    """Lista todos os tenants (clientes) cadastrados."""
    tenants = Tenant.objects.using('default').all().order_by('nome')
    context = {
        'tenants': tenants,
        'data_page': 'tenant_list',
    }
    return render_ajax_or_base(request, 'partials/control/tenant_list.html', context)

@superuser_required
@principal_context_required
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
@principal_context_required
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
@principal_context_required
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
@principal_context_required
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
@principal_context_required
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
@permission_required('control.view_emitente', raise_exception=True)
def lista_emitentes(request):
    """
    Lista todos os emitentes cadastrados no banco de dados atual.
    """
    emitentes = Emitente.objects.all().order_by('-is_default', 'nome_fantasia')
    context = {'emitentes': emitentes}
    return render_ajax_or_base(request, 'partials/control/lista_emitentes.html', context)

@login_required
@permission_required('control.add_emitente', raise_exception=True)
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
@permission_required('control.change_emitente', raise_exception=True)
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
@permission_required('control.delete_emitente', raise_exception=True)
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
