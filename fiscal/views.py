import io
import json

import openpyxl
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q, Case, When, Value, IntegerField
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from common.messages_utils import get_app_messages
from common.utils.rendering import render_ajax_or_base
from .fiscal_services import (
    consolidate_duplicates,
    import_local_data_to_db,
    inspect_duplicates,
    summarize_local_data,
    update_local_data_from_excel,
)
from .forms import CfopForm, NaturezaOperacaoForm, UploadExcelForm
from .models import Cfop, NaturezaOperacao


FISCAL_LABELS = {
    'cfop': 'CFOP',
    'natureza_operacao': 'Natureza de Opera\u00e7\u00e3o',
}


# --- Helpers ---

def _ensure_any_fiscal_import_permission(user):
    if user.has_perm('fiscal.add_cfop') or user.has_perm('fiscal.add_naturezaoperacao'):
        return
    raise PermissionDenied


def _ensure_import_permission_for_type(user, import_type):
    if import_type == 'cfop' and user.has_perm('fiscal.add_cfop'):
        return
    if import_type == 'natureza_operacao' and user.has_perm('fiscal.add_naturezaoperacao'):
        return
    raise PermissionDenied


def _ensure_delete_permission_for_type(user, item_type):
    if item_type == 'cfop' and user.has_perm('fiscal.delete_cfop'):
        return
    if item_type == 'natureza_operacao' and user.has_perm('fiscal.delete_naturezaoperacao'):
        return
    raise PermissionDenied


def _get_fiscal_import_back_url(user):
    if user.has_perm('fiscal.view_cfop'):
        return reverse('fiscal:cfop_list')
    if user.has_perm('fiscal.view_naturezaoperacao'):
        return reverse('fiscal:natureza_operacao_list')
    return '/'


def _build_import_context(user, form=None):
    return {
        'form': form or UploadExcelForm(),
        'content_template': 'partials/fiscal/import_fiscal_data.html',
        'data_page': 'import_fiscal_data',
        'title': 'Importar Dados Fiscais (Excel)',
        'back_url': _get_fiscal_import_back_url(user),
        'cfop_local_summary': summarize_local_data('cfop'),
        'natureza_local_summary': summarize_local_data('natureza_operacao'),
        'cfop_source_path': r'OneTech\fiscal\cfops.xlsx',
        'natureza_source_path': 'OneTech\\fiscal\\natureza_opera\u00e7\u00e3o.xlsx',
    }


# --- Views para CFOP ---

@login_required
@permission_required('fiscal.view_cfop', raise_exception=True)
def cfop_list(request):
    ordenacao = request.GET.get('ordenacao', 'codigo')
    termo_busca = request.GET.get('busca', '').strip()

    valid_sort_fields = ['codigo', 'descricao', 'categoria']
    field = ordenacao[1:] if ordenacao.startswith('-') else ordenacao
    if field not in valid_sort_fields:
        ordenacao = 'codigo'

    cfops = Cfop.objects.all()
    if termo_busca:
        cfops = cfops.filter(
            Q(codigo__icontains=termo_busca)
            | Q(descricao__icontains=termo_busca)
            | Q(categoria__icontains=termo_busca)
        )

        # Prioriza resultados mais relevantes para o termo informado.
        # Ordem: codigo exato, codigo iniciando pelo termo, descricao iniciando,
        # categoria iniciando e, por fim, qualquer ocorrencia no meio do texto.
        cfops = cfops.annotate(
            busca_rank=Case(
                When(codigo__iexact=termo_busca, then=Value(0)),
                When(codigo__istartswith=termo_busca, then=Value(1)),
                When(descricao__istartswith=termo_busca, then=Value(2)),
                When(categoria__istartswith=termo_busca, then=Value(3)),
                default=Value(9),
                output_field=IntegerField(),
            )
        )

    context = {
        'cfops': cfops.order_by('busca_rank', ordenacao, 'codigo') if termo_busca else cfops.order_by(ordenacao),
        'ordenacao_atual': ordenacao,
        'termo_busca': termo_busca,
        'content_template': 'partials/fiscal/cfop_list.html',
        'data_page': 'cfop_list',
    }
    return render_ajax_or_base(request, context['content_template'], context)


@login_required
@permission_required('fiscal.add_cfop', raise_exception=True)
def cfop_create(request):
    app_messages = get_app_messages(request)
    if request.method == 'POST':
        form = CfopForm(request.POST)
        if form.is_valid():
            form.save()
            app_messages.success_created(form.instance)
            return redirect('fiscal:cfop_list')
    else:
        form = CfopForm()

    return render(request, 'base.html', {
        'form': form,
        'content_template': 'partials/fiscal/cfop_form.html',
        'data_page': 'cfop_create',
        'title': 'Cadastrar CFOP',
    })


@login_required
@permission_required('fiscal.change_cfop', raise_exception=True)
def cfop_update(request, pk):
    app_messages = get_app_messages(request)
    cfop = get_object_or_404(Cfop, pk=pk)
    if request.method == 'POST':
        form = CfopForm(request.POST, instance=cfop)
        if form.is_valid():
            form.save()
            app_messages.success_updated(form.instance)
            return redirect('fiscal:cfop_list')
    else:
        form = CfopForm(instance=cfop)

    return render(request, 'base.html', {
        'form': form,
        'content_template': 'partials/fiscal/cfop_form.html',
        'data_page': 'cfop_update',
        'title': 'Editar CFOP',
    })


# --- Views para Natureza de Operacao ---

@login_required
@permission_required('fiscal.view_naturezaoperacao', raise_exception=True)
def natureza_operacao_list(request):
    ordenacao = request.GET.get('ordenacao', 'descricao')
    termo_busca = request.GET.get('busca', '').strip()

    valid_sort_fields = ['codigo', 'descricao', 'observacoes']
    field = ordenacao[1:] if ordenacao.startswith('-') else ordenacao
    if field not in valid_sort_fields:
        ordenacao = 'descricao'

    naturezas = NaturezaOperacao.objects.all()
    if termo_busca:
        naturezas = naturezas.filter(
            Q(codigo__icontains=termo_busca)
            | Q(descricao__icontains=termo_busca)
            | Q(observacoes__icontains=termo_busca)
        )

    context = {
        'naturezas': naturezas.order_by(ordenacao),
        'ordenacao_atual': ordenacao,
        'termo_busca': termo_busca,
        'content_template': 'partials/fiscal/natureza_operacao_list.html',
        'data_page': 'natureza_operacao_list',
    }
    return render_ajax_or_base(request, context['content_template'], context)


@login_required
@permission_required('fiscal.add_naturezaoperacao', raise_exception=True)
def natureza_operacao_create(request):
    app_messages = get_app_messages(request)
    if request.method == 'POST':
        form = NaturezaOperacaoForm(request.POST)
        if form.is_valid():
            form.save()
            app_messages.success_created(form.instance)
            return redirect('fiscal:natureza_operacao_list')
    else:
        form = NaturezaOperacaoForm()

    return render(request, 'base.html', {
        'form': form,
        'content_template': 'partials/fiscal/natureza_operacao_form.html',
        'data_page': 'natureza_operacao_create',
        'title': 'Cadastrar Natureza de Opera\u00e7\u00e3o',
    })


@login_required
@permission_required('fiscal.change_naturezaoperacao', raise_exception=True)
def natureza_operacao_update(request, pk):
    app_messages = get_app_messages(request)
    natureza = get_object_or_404(NaturezaOperacao, pk=pk)
    if request.method == 'POST':
        form = NaturezaOperacaoForm(request.POST, instance=natureza)
        if form.is_valid():
            form.save()
            app_messages.success_updated(form.instance)
            return redirect('fiscal:natureza_operacao_list')
    else:
        form = NaturezaOperacaoForm(instance=natureza)

    return render(request, 'base.html', {
        'form': form,
        'content_template': 'partials/fiscal/natureza_operacao_form.html',
        'data_page': 'natureza_operacao_update',
        'title': 'Editar Natureza de Opera\u00e7\u00e3o',
    })


# --- Central de Importacao Fiscal ---

@login_required
def import_fiscal_data_view(request):
    app_messages = get_app_messages(request)
    _ensure_any_fiscal_import_permission(request.user)

    form = UploadExcelForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            excel_file = form.cleaned_data['excel_file']
            import_type = form.cleaned_data['import_type']
            _ensure_import_permission_for_type(request.user, import_type)
            payload = update_local_data_from_excel(excel_file, import_type)
            count = payload['metadata']['item_count']
            app_messages.success_process(
                f'Base local de {FISCAL_LABELS[import_type]} atualizada com sucesso. {count} registro(s) salvos em disco.'
            )
            return redirect('fiscal:import_fiscal_data')

        errors = []
        for field, field_errors in form.errors.items():
            for error in field_errors:
                errors.append(f"Campo '{field}': {error}")
        app_messages.error('Erro no formul\u00e1rio de importa\u00e7\u00e3o: ' + '; '.join(errors))

    context = _build_import_context(request.user, form=form)
    return render_ajax_or_base(request, context['content_template'], context)


@login_required
@require_POST
def import_fiscal_local_view(request):
    app_messages = get_app_messages(request)
    import_type = request.POST.get('import_type', '').strip()
    _ensure_import_permission_for_type(request.user, import_type)

    try:
        result = import_local_data_to_db(import_type)
        app_messages.success_process(
            f"{result['count']} registro(s) de {FISCAL_LABELS[import_type]} importados/atualizados a partir da base local."
        )
    except FileNotFoundError:
        app_messages.error(f'Arquivo local de {FISCAL_LABELS.get(import_type, import_type)} n?o encontrado.')
    except ValueError as exc:
        app_messages.error(str(exc))
    except Exception as exc:
        app_messages.error(f'Erro ao importar base local: {exc}')

    return redirect('fiscal:import_fiscal_data')


@login_required
@require_POST
def consolidar_fiscal_view(request):
    app_messages = get_app_messages(request)
    import_type = request.POST.get('import_type', '').strip()
    apply_changes = request.POST.get('apply') == '1'

    if import_type == 'cfop':
        required_perm = 'fiscal.delete_cfop'
    else:
        required_perm = 'fiscal.delete_naturezaoperacao'
    if not request.user.has_perm(required_perm):
        raise PermissionDenied

    try:
        summary = consolidate_duplicates(import_type) if apply_changes else inspect_duplicates(import_type)
        if summary['group_count'] == 0:
            app_messages.success_process(f'Nenhuma duplicidade de {FISCAL_LABELS[import_type]} encontrada.')
        elif apply_changes:
            app_messages.success_process(
                f"Consolida\u00e7\u00e3o conclu\u00edda para {FISCAL_LABELS[import_type]}. {summary['group_count']} grupo(s) tratados."
            )
        else:
            app_messages.warning(
                f"{summary['group_count']} grupo(s) com duplicidade detectado(s) em {FISCAL_LABELS[import_type]}."
            )
    except ValueError as exc:
        app_messages.error(str(exc))
    except Exception as exc:
        app_messages.error(f'Erro ao consolidar dados fiscais: {exc}')

    return redirect('fiscal:import_fiscal_data')


@login_required
def download_fiscal_template_view(request):
    app_messages = get_app_messages(request)
    import_type = request.GET.get('type')
    _ensure_any_fiscal_import_permission(request.user)

    if import_type == 'cfop':
        _ensure_import_permission_for_type(request.user, import_type)
        headers = ['codigo', 'descricao', 'categoria']
        filename = 'template_cfop.xlsx'
    elif import_type == 'natureza_operacao':
        _ensure_import_permission_for_type(request.user, import_type)
        headers = ['codigo', 'descricao', 'observacoes']
        filename = 'template_natureza_operacao.xlsx'
    else:
        app_messages.error('Tipo de template inv?lido.')
        return redirect('fiscal:import_fiscal_data')

    output = io.BytesIO()
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Dados Fiscais'
    sheet.append(headers)
    workbook.save(output)
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response


@login_required
@require_POST
def delete_fiscal_items(request):
    app_messages = get_app_messages(request)
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        item_type = data.get('item_type')
        _ensure_delete_permission_for_type(request.user, item_type)

        if not ids:
            message = app_messages.error('Nenhum ID fornecido para exclus?o.')
            return JsonResponse({'success': False, 'message': message}, status=400)

        with transaction.atomic():
            if item_type == 'cfop':
                model = Cfop
                model_name = 'CFOP'
            elif item_type == 'natureza_operacao':
                model = NaturezaOperacao
                model_name = 'Natureza de Opera\u00e7\u00e3o'
            else:
                message = app_messages.error('Tipo de item inv?lido.')
                return JsonResponse({'success': False, 'message': message}, status=400)

            deleted_count, _ = model.objects.filter(pk__in=ids).delete()

        message = app_messages.success_deleted(model_name, f'{deleted_count} selecionado(s)')
        return JsonResponse({'success': True, 'message': message})

    except json.JSONDecodeError:
        message = app_messages.error('Requisi\u00e7\u00e3o inv\u00e1lida. JSON malformado.')
        return JsonResponse({'success': False, 'message': message}, status=400)
    except PermissionDenied:
        message = app_messages.error('Voc? n?o tem permiss?o para excluir estes itens.')
        return JsonResponse({'success': False, 'message': message}, status=403)
    except Exception as exc:
        message = app_messages.error(f'Erro ao excluir itens fiscais: {exc}')
        return JsonResponse({'success': False, 'message': message}, status=500)

# --- Overrides para fluxo ICMS Origem x Destino na Central Fiscal ---

FISCAL_LABELS['icms_origem_destino'] = 'ICMS Origem x Destino'


def _ensure_any_fiscal_import_permission(user):
    if (
        user.has_perm('fiscal.add_cfop')
        or user.has_perm('fiscal.add_naturezaoperacao')
        or user.has_perm('fiscal_regras.add_regraaliquotaicms')
    ):
        return
    raise PermissionDenied


def _ensure_import_permission_for_type(user, import_type):
    if import_type == 'cfop' and user.has_perm('fiscal.add_cfop'):
        return
    if import_type == 'natureza_operacao' and user.has_perm('fiscal.add_naturezaoperacao'):
        return
    if import_type == 'icms_origem_destino' and user.has_perm('fiscal_regras.add_regraaliquotaicms'):
        return
    raise PermissionDenied


def _build_import_context(user, form=None):
    return {
        'form': form or UploadExcelForm(),
        'content_template': 'partials/fiscal/import_fiscal_data.html',
        'data_page': 'import_fiscal_data',
        'title': 'Importar Dados Fiscais (Excel)',
        'back_url': _get_fiscal_import_back_url(user),
        'cfop_local_summary': summarize_local_data('cfop'),
        'natureza_local_summary': summarize_local_data('natureza_operacao'),
        'icms_matriz_local_summary': summarize_local_data('icms_origem_destino'),
        'cfop_source_path': r'OneTech\fiscal\cfops.xlsx',
        'natureza_source_path': 'OneTech\\fiscal\\natureza_operacao.xlsx',
        'icms_matriz_source_path': 'OneTech\\fiscal\\icms_origem_destino.xlsx',
    }


@login_required
@require_POST
def import_fiscal_local_view(request):
    app_messages = get_app_messages(request)
    import_type = request.POST.get('import_type', '').strip()
    _ensure_import_permission_for_type(request.user, import_type)

    try:
        result = import_local_data_to_db(import_type)
        if import_type == 'icms_origem_destino':
            app_messages.success_process(
                f"{result['count']} regra(s) de ICMS geradas/atualizadas em fiscal_regras a partir da matriz local "
                f"({result.get('linhas_matriz', 0)} linha(s) x {result.get('ncm_count', 0)} NCM(s))."
            )
        else:
            app_messages.success_process(
                f"{result['count']} registro(s) de {FISCAL_LABELS[import_type]} importados/atualizados a partir da base local."
            )
    except FileNotFoundError:
        app_messages.error(f"Arquivo local de {FISCAL_LABELS.get(import_type, import_type)} nao encontrado.")
    except ValueError as exc:
        app_messages.error(str(exc))
    except Exception as exc:
        app_messages.error(f'Erro ao importar base local: {exc}')

    return redirect('fiscal:import_fiscal_data')


@login_required
@require_POST
def consolidar_fiscal_view(request):
    app_messages = get_app_messages(request)
    import_type = request.POST.get('import_type', '').strip()
    apply_changes = request.POST.get('apply') == '1'

    if import_type == 'cfop':
        required_perm = 'fiscal.delete_cfop'
    elif import_type == 'natureza_operacao':
        required_perm = 'fiscal.delete_naturezaoperacao'
    else:
        app_messages.warning('Consolidacao nao se aplica para ICMS Origem x Destino.')
        return redirect('fiscal:import_fiscal_data')

    if not request.user.has_perm(required_perm):
        raise PermissionDenied

    try:
        summary = consolidate_duplicates(import_type) if apply_changes else inspect_duplicates(import_type)
        if summary['group_count'] == 0:
            app_messages.success_process(f"Nenhuma duplicidade de {FISCAL_LABELS[import_type]} encontrada.")
        elif apply_changes:
            app_messages.success_process(
                f"Consolidacao concluida para {FISCAL_LABELS[import_type]}. {summary['group_count']} grupo(s) tratados."
            )
        else:
            app_messages.warning(
                f"{summary['group_count']} grupo(s) com duplicidade detectado(s) em {FISCAL_LABELS[import_type]}."
            )
    except ValueError as exc:
        app_messages.error(str(exc))
    except Exception as exc:
        app_messages.error(f'Erro ao consolidar dados fiscais: {exc}')

    return redirect('fiscal:import_fiscal_data')


@login_required
def download_fiscal_template_view(request):
    app_messages = get_app_messages(request)
    import_type = request.GET.get('type')
    _ensure_any_fiscal_import_permission(request.user)

    if import_type == 'cfop':
        _ensure_import_permission_for_type(request.user, import_type)
        headers = ['codigo', 'descricao', 'categoria']
        filename = 'template_cfop.xlsx'
    elif import_type == 'natureza_operacao':
        _ensure_import_permission_for_type(request.user, import_type)
        headers = ['codigo', 'descricao', 'observacoes']
        filename = 'template_natureza_operacao.xlsx'
    elif import_type == 'icms_origem_destino':
        _ensure_import_permission_for_type(request.user, import_type)
        headers = [
            'uf_origem', 'uf_destino', 'aliquota_icms', 'fcp', 'reducao_base_icms',
            'modalidade', 'tipo_operacao', 'origem_mercadoria', 'vigencia_inicio',
            'vigencia_fim', 'prioridade', 'ativo', 'descricao'
        ]
        filename = 'template_icms_origem_destino.xlsx'
    else:
        app_messages.error('Tipo de template invalido.')
        return redirect('fiscal:import_fiscal_data')

    output = io.BytesIO()
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Dados Fiscais'
    sheet.append(headers)
    workbook.save(output)
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response
