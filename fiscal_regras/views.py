import json

from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET, require_POST

from common.messages_utils import get_app_messages
from common.utils.rendering import render_ajax_or_base

from .forms import RegraAliquotaICMSForm
from .models import RegraAliquotaICMS
from .services import resolver_regra_icms_item


@login_required
@permission_required('fiscal_regras.view_regraaliquotaicms', raise_exception=True)
def regra_icms_list(request):
    ordenacao = request.GET.get('ordenacao', '-prioridade')
    termo_busca = (request.GET.get('busca') or '').strip()

    valid_sort_fields = ['descricao', 'ncm_prefixo', 'aliquota_icms', 'prioridade', 'vigencia_inicio', 'vigencia_fim']
    sort_field = ordenacao[1:] if ordenacao.startswith('-') else ordenacao
    if sort_field not in valid_sort_fields:
        ordenacao = '-prioridade'

    regras = RegraAliquotaICMS.objects.all()
    if termo_busca:
        regras = regras.filter(
            Q(descricao__icontains=termo_busca)
            | Q(ncm_prefixo__icontains=termo_busca)
            | Q(uf_origem__icontains=termo_busca)
            | Q(uf_destino__icontains=termo_busca)
            | Q(observacoes__icontains=termo_busca)
        )

    context = {
        'regras': regras.order_by(ordenacao),
        'ordenacao_atual': ordenacao,
        'termo_busca': termo_busca,
        'content_template': 'partials/fiscal_regras/regra_icms_list.html',
        'data_page': 'regra_icms_list',
    }
    return render_ajax_or_base(request, context['content_template'], context)


@login_required
@permission_required('fiscal_regras.add_regraaliquotaicms', raise_exception=True)
def regra_icms_create(request):
    app_messages = get_app_messages(request)

    if request.method == 'POST':
        form = RegraAliquotaICMSForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.updated_by = request.user
            obj.save()
            app_messages.success_created(obj)
            return redirect('fiscal_regras:regra_icms_list')
    else:
        form = RegraAliquotaICMSForm()

    return render(request, 'base.html', {
        'form': form,
        'content_template': 'partials/fiscal_regras/regra_icms_form.html',
        'data_page': 'regra_icms_create',
        'title': 'Cadastrar Regra ICMS',
    })


@login_required
@permission_required('fiscal_regras.change_regraaliquotaicms', raise_exception=True)
def regra_icms_update(request, pk):
    app_messages = get_app_messages(request)
    regra = get_object_or_404(RegraAliquotaICMS, pk=pk)

    if request.method == 'POST':
        form = RegraAliquotaICMSForm(request.POST, instance=regra)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.updated_by = request.user
            obj.save()
            app_messages.success_updated(obj)
            return redirect('fiscal_regras:regra_icms_list')
    else:
        form = RegraAliquotaICMSForm(instance=regra)

    return render(request, 'base.html', {
        'form': form,
        'content_template': 'partials/fiscal_regras/regra_icms_form.html',
        'data_page': 'regra_icms_update',
        'title': 'Editar Regra ICMS',
    })


@login_required
@permission_required('fiscal_regras.delete_regraaliquotaicms', raise_exception=True)
@require_POST
def delete_regras_icms(request):
    app_messages = get_app_messages(request)

    try:
        payload = json.loads(request.body.decode('utf-8'))
        ids = payload.get('ids', [])
        if not ids:
            return JsonResponse({'success': False, 'message': app_messages.error('Nenhum ID informado para exclusao.')}, status=400)

        deleted_count, _ = RegraAliquotaICMS.objects.filter(pk__in=ids).delete()
        return JsonResponse({'success': True, 'message': app_messages.success_deleted('Regra ICMS', f'{deleted_count} selecionada(s)')})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': app_messages.error('JSON invalido.')}, status=400)
    except Exception as exc:
        return JsonResponse({'success': False, 'message': app_messages.error(f'Erro ao excluir regras: {exc}')}, status=500)


@login_required
@permission_required('fiscal_regras.view_regraaliquotaicms', raise_exception=True)
@require_GET
def resolver_aliquota_icms_api(request):
    data_emissao = parse_date((request.GET.get('data_emissao') or '').strip())

    resolucao = resolver_regra_icms_item(
        data_emissao=data_emissao,
        emitente_id=request.GET.get('emitente_id') or None,
        destinatario_id=request.GET.get('destinatario_id') or None,
        uf_emitente=request.GET.get('uf_emitente') or None,
        uf_destino=request.GET.get('uf_destino') or None,
        ncm=request.GET.get('ncm') or None,
        tipo_operacao=(request.GET.get('tipo_operacao') or '1').strip(),
        origem_mercadoria=request.GET.get('origem_mercadoria') or None,
        produto_id=request.GET.get('produto_id') or None,
    )

    return JsonResponse({
        'success': True,
        'found': resolucao.found,
        'origem': resolucao.origem,
        'aliquota_icms': str(resolucao.aliquota_icms),
        'reducao_base_icms': str(resolucao.reducao_base_icms),
        'fcp': str(resolucao.fcp),
        'regra_id': resolucao.regra_id,
        'regra_descricao': resolucao.regra_descricao,
        'cst_icms_id': resolucao.cst_icms_id,
        'csosn_icms_id': resolucao.csosn_icms_id,
        'aliquota_ipi': str(resolucao.aliquota_ipi) if resolucao.aliquota_ipi is not None else '',
        'aliquota_pis': str(resolucao.aliquota_pis) if resolucao.aliquota_pis is not None else '',
        'aliquota_cofins': str(resolucao.aliquota_cofins) if resolucao.aliquota_cofins is not None else '',
        'contexto': resolucao.contexto,
    })


@login_required
@permission_required('fiscal_regras.add_regraaliquotaicms', raise_exception=True)
@require_POST
def importar_regras_view(request):
    return JsonResponse({'success': False, 'message': 'Importacao via interface sera disponibilizada na proxima etapa.'}, status=501)


@login_required
@permission_required('fiscal_regras.view_regraaliquotaicms', raise_exception=True)
@require_POST
def validar_regras_view(request):
    return JsonResponse({'success': True, 'message': 'Validacao basica concluida.'})


@login_required
@permission_required('fiscal_regras.view_regraaliquotaicms', raise_exception=True)
@require_GET
def exportar_regras_view(request):
    data = list(
        RegraAliquotaICMS.objects.values(
            'id', 'ativo', 'descricao', 'ncm_prefixo', 'tipo_operacao', 'modalidade',
            'uf_origem', 'uf_destino', 'origem_mercadoria', 'aliquota_icms', 'fcp',
            'reducao_base_icms', 'prioridade', 'vigencia_inicio', 'vigencia_fim',
        )
    )
    return JsonResponse({'count': len(data), 'results': data})
