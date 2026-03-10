import json

from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from common.messages_utils import get_app_messages
from common.utils.rendering import render_ajax_or_base

from .forms import CondicaoPagamentoForm
from .models import CondicaoPagamento


@login_required
@permission_required('comercial.view_condicaopagamento', raise_exception=True)
def condicao_pagamento_list(request):
    ordenacao = request.GET.get('ordenacao', 'codigo')
    termo_busca = request.GET.get('busca', '').strip()

    valid_sort_fields = ['codigo', 'descricao', 'quantidade_parcelas', 'observacoes']
    field = ordenacao[1:] if ordenacao.startswith('-') else ordenacao
    if field not in valid_sort_fields:
        ordenacao = 'codigo'

    condicoes = CondicaoPagamento.objects.all()
    if termo_busca:
        condicoes = condicoes.filter(
            Q(codigo__icontains=termo_busca)
            | Q(descricao__icontains=termo_busca)
            | Q(observacoes__icontains=termo_busca)
        )

    context = {
        'condicoes': condicoes.order_by(ordenacao),
        'ordenacao_atual': ordenacao,
        'termo_busca': termo_busca,
        'content_template': 'comercial/condicao_pagamento_list.html',
        'data_page': 'condicao_pagamento_list',
    }
    return render_ajax_or_base(request, context['content_template'], context)


@login_required
@permission_required('comercial.add_condicaopagamento', raise_exception=True)
def condicao_pagamento_create(request):
    app_messages = get_app_messages(request)
    if request.method == 'POST':
        form = CondicaoPagamentoForm(request.POST)
        if form.is_valid():
            form.save()
            app_messages.success_created(form.instance)
            return redirect('comercial:condicao_pagamento_list')
    else:
        form = CondicaoPagamentoForm()

    return render(request, 'base.html', {
        'form': form,
        'content_template': 'comercial/condicao_pagamento_form.html',
        'data_page': 'condicao_pagamento_create',
        'title': 'Cadastrar Condicao de Pagamento',
    })


@login_required
@permission_required('comercial.change_condicaopagamento', raise_exception=True)
def condicao_pagamento_update(request, pk):
    app_messages = get_app_messages(request)
    condicao = get_object_or_404(CondicaoPagamento, pk=pk)

    if request.method == 'POST':
        form = CondicaoPagamentoForm(request.POST, instance=condicao)
        if form.is_valid():
            form.save()
            app_messages.success_updated(form.instance)
            return redirect('comercial:condicao_pagamento_list')
    else:
        form = CondicaoPagamentoForm(instance=condicao)

    return render(request, 'base.html', {
        'form': form,
        'content_template': 'comercial/condicao_pagamento_form.html',
        'data_page': 'condicao_pagamento_update',
        'title': 'Editar Condicao de Pagamento',
    })


@login_required
@permission_required('comercial.delete_condicaopagamento', raise_exception=True)
@require_POST
def delete_condicoes_pagamento(request):
    app_messages = get_app_messages(request)

    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])

        if not ids:
            return JsonResponse({'success': False, 'message': app_messages.error('Nenhum ID informado para exclusao.')}, status=400)

        deleted_count, _ = CondicaoPagamento.objects.filter(pk__in=ids).delete()
        message = app_messages.success_deleted('Condicao de Pagamento', f'{deleted_count} selecionada(s)')
        return JsonResponse({'success': True, 'message': message})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': app_messages.error('JSON invalido.')}, status=400)
    except Exception as exc:
        return JsonResponse({'success': False, 'message': app_messages.error(f'Erro ao excluir condicoes de pagamento: {exc}')}, status=500)
