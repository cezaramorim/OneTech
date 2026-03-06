import json

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from accounts.utils.decorators import login_required_json
from common.messages_utils import get_app_messages
from common.mixins import AjaxListMixin
from common.utils import render_ajax_or_base
from .forms import CategoriaEmpresaForm, EmpresaForm
from .models import CategoriaEmpresa, EmpresaAvancada


# === Categorias ===

@login_required_json
@permission_required('empresas.view_categoriaempresa', raise_exception=True)
def lista_categorias_view(request):
    categorias = CategoriaEmpresa.objects.all().order_by('nome')
    return render_ajax_or_base(request, 'partials/empresas/lista_categorias.html', {
        'categorias': categorias
    })


@login_required_json
def categoria_form_view(request, pk=None):
    app_messages = get_app_messages(request)

    if pk:
        if not request.user.has_perm('empresas.change_categoriaempresa'):
            message = app_messages.error('Você não tem permissão para editar categorias.')
            return JsonResponse({'success': False, 'message': message}, status=403)
        categoria = get_object_or_404(CategoriaEmpresa, pk=pk)
    else:
        if not request.user.has_perm('empresas.add_categoriaempresa'):
            message = app_messages.error('Você não tem permissão para adicionar categorias.')
            return JsonResponse({'success': False, 'message': message}, status=403)
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
            return redirect('empresas:lista_empresas')

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(
                {
                    'success': False,
                    'errors': form.errors,
                    'message': app_messages.error('Erro ao salvar categoria. Verifique os campos.'),
                },
                status=400,
            )
        app_messages.error('Erro ao salvar categoria. Verifique os campos.')

    context = {
        'form': form,
    }
    return render_ajax_or_base(request, 'partials/empresas/categoria_form.html', context)


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

        message = app_messages.success_deleted('Categoria(s)', f'{count} selecionada(s)')
        return JsonResponse({'success': True, 'message': message, 'redirect_url': reverse('empresas:lista_categorias')})
    except json.JSONDecodeError:
        message = app_messages.error('Requisição inválida (JSON malformatado).')
        return JsonResponse({'success': False, 'message': message}, status=400)
    except Exception as exc:
        message = app_messages.error(f'Erro ao excluir categorias: {str(exc)}')
        return JsonResponse({'success': False, 'message': message}, status=500)


# === Empresas (cadastro e edicao) ===
@login_required_json
@permission_required('empresas.add_empresaavancada', raise_exception=True)
def empresa_form_view(request, pk=None):
    app_messages = get_app_messages(request)
    if pk:
        empresa = get_object_or_404(EmpresaAvancada, pk=pk)
    else:
        empresa = None

    form = EmpresaForm(request.POST or None, instance=empresa)

    if request.method == 'POST':
        if form.is_valid():
            form.save()

            if pk:
                message = app_messages.success_updated(form.instance)
            else:
                message = app_messages.success_created(form.instance)

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse(
                    {
                        'success': True,
                        'message': message,
                        'redirect_url': reverse('empresas:lista_empresas'),
                    }
                )

            return redirect('empresas:lista_empresas')

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            message = app_messages.error('Erro ao salvar empresa. Verifique os campos.')
            return JsonResponse({'success': False, 'message': message, 'errors': form.errors}, status=400)
        app_messages.error('Erro ao salvar empresa. Verifique os campos.')

    context = {
        'form': form,
        'vendedores': get_user_model().objects.filter(groups__name__iexact='vendedores').order_by('first_name'),
        'estados': [
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
            'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
            'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
        ],
        'empresa': empresa,
    }
    return render_ajax_or_base(request, 'partials/empresas/cadastrar_empresa.html', context)


@login_required_json
def lista_empresas_view(request):
    """
    View que lista empresas com suporte a:
    - filtro unificado por termo (razao social, nome fantasia, nome, CNPJ ou CPF)
    - filtro por tipo de empresa (PF ou PJ)
    - filtro por status (ativa/inativa)
    - compativel com AJAX e base.html
    """
    empresas = EmpresaAvancada.objects.select_related('categoria').all()
    termo = request.GET.get('termo_empresa', '').strip()
    tipo = request.GET.get('tipo', '').strip().lower()
    status = request.GET.get('status', '').strip()

    if termo:
        empresas = empresas.filter(
            Q(razao_social__icontains=termo)
            | Q(cnpj__icontains=termo)
            | Q(nome__icontains=termo)
            | Q(nome_fantasia__icontains=termo)
            | Q(cpf__icontains=termo)
        )
    if tipo in {'pj', 'pf'}:
        empresas = empresas.filter(tipo_empresa=tipo)
    if status:
        status_map = {'ativo': 'ativa', 'inativo': 'inativa'}
        if status in status_map:
            empresas = empresas.filter(status_empresa=status_map[status])

    context = {'empresas': empresas, 'request': request}

    mixin = AjaxListMixin()
    mixin.template_page = 'partials/empresas/lista_empresas.html'
    mixin.template_partial = 'partials/empresas/_lista_empresas_table.html'
    return mixin.render_list(request, context)


@login_required_json
@csrf_exempt
@require_POST
def atualizar_status_empresa(request, pk):
    app_messages = get_app_messages(request)
    try:
        data = json.loads(request.body)
        empresa = EmpresaAvancada.objects.get(pk=pk)
        ativo = data.get('ativo', False)
        empresa.status_empresa = 'ativa' if ativo else 'inativa'
        empresa.save(update_fields=['status_empresa'])
        message = app_messages.success_updated(
            empresa,
            custom_message=f'Status da empresa "{empresa.razao_social or empresa.nome}" atualizado com sucesso.',
        )
        return JsonResponse({'success': True, 'message': message})
    except Exception:
        message = app_messages.error('Erro ao atualizar o status da empresa.')
        return JsonResponse({'success': False, 'message': message}, status=500)


@require_POST
@login_required_json
@permission_required('empresas.delete_empresaavancada', raise_exception=True)
def excluir_empresas_view(request):
    app_messages = get_app_messages(request)
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        if not ids:
            message = app_messages.error('Nenhum ID fornecido.')
            return JsonResponse({'success': False, 'message': message}, status=400)

        count = len(ids)
        EmpresaAvancada.objects.filter(pk__in=ids).delete()

        message = app_messages.success_deleted('Empresa(s)', f'{count} selecionada(s)')
        return JsonResponse(
            {
                'success': True,
                'message': message,
                'redirect_url': reverse('empresas:lista_empresas'),
            }
        )
    except json.JSONDecodeError:
        message = app_messages.error('Requisição inválida (JSON malformatado).')
        return JsonResponse({'success': False, 'message': message}, status=400)
    except Exception as exc:
        message = app_messages.error(f'Erro ao excluir empresas: {str(exc)}')
        return JsonResponse({'success': False, 'message': message}, status=500)

