import io
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

from .models import Cfop, NaturezaOperacao
from .forms import CfopForm, NaturezaOperacaoForm

# Certifique-se de ter o openpyxl instalado: pip install openpyxl
import openpyxl

# --- Views para CFOP ---

@login_required
def cfop_list(request):
    ordenacao = request.GET.get('ordenacao', 'codigo') # Padrão: ordenar por código
    termo_busca = request.GET.get('busca', '').strip()

    # Garante que a ordenação seja válida para evitar erros
    valid_sort_fields = ['codigo', 'descricao', 'categoria']
    if ordenacao.startswith('-'):
        field = ordenacao[1:]
    else:
        field = ordenacao

    if field not in valid_sort_fields:
        ordenacao = 'codigo' # Volta para o padrão se o campo for inválido

    cfops = Cfop.objects.all()

    if termo_busca:
        cfops = cfops.filter(
            Q(codigo__icontains=termo_busca) |
            Q(descricao__icontains=termo_busca) |
            Q(categoria__icontains=termo_busca)
        )

    cfops = cfops.order_by(ordenacao)
    context = {
        'cfops': cfops,
        'ordenacao_atual': ordenacao,
        'termo_busca': termo_busca,
        'content_template': 'partials/fiscal/cfop_list.html',
        'data_page': 'cfop_list',
    }
    return render(request, 'base.html', context)

@login_required
def cfop_create(request):
    if request.method == 'POST':
        form = CfopForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'CFOP cadastrado com sucesso!')
            return redirect('fiscal:cfop_list')
    else:
        form = CfopForm()
    
    context = {
        'form': form,
        'content_template': 'partials/fiscal/cfop_form.html',
        'data_page': 'cfop_create',
        'title': 'Cadastrar CFOP',
    }
    return render(request, 'base.html', context)

@login_required
def cfop_update(request, pk):
    cfop = get_object_or_404(Cfop, pk=pk)
    if request.method == 'POST':
        form = CfopForm(request.POST, instance=cfop)
        if form.is_valid():
            form.save()
            messages.success(request, 'CFOP atualizado com sucesso!')
            return redirect('fiscal:cfop_list')
    else:
        form = CfopForm(instance=cfop)
    
    context = {
        'form': form,
        'content_template': 'partials/fiscal/cfop_form.html',
        'data_page': 'cfop_update',
        'title': 'Editar CFOP',
    }
    return render(request, 'base.html', context)

# --- Views para Natureza de Operação ---

@login_required
def natureza_operacao_list(request):
    ordenacao = request.GET.get('ordenacao', 'descricao') # Padrão: ordenar por descrição
    termo_busca = request.GET.get('busca', '').strip()

    # Garante que a ordenação seja válida para evitar erros
    valid_sort_fields = ['codigo', 'descricao', 'observacoes']
    if ordenacao.startswith('-'):
        field = ordenacao[1:]
    else:
        field = ordenacao

    if field not in valid_sort_fields:
        ordenacao = 'descricao' # Volta para o padrão se o campo for inválido

    naturezas = NaturezaOperacao.objects.all()

    if termo_busca:
        naturezas = naturezas.filter(
            Q(codigo__icontains=termo_busca) |
            Q(descricao__icontains=termo_busca) |
            Q(observacoes__icontains=termo_busca)
        )

    naturezas = naturezas.order_by(ordenacao)
    context = {
        'naturezas': naturezas,
        'ordenacao_atual': ordenacao,
        'termo_busca': termo_busca,
        'content_template': 'partials/fiscal/natureza_operacao_list.html',
        'data_page': 'natureza_operacao_list',
    }
    return render(request, 'base.html', context)

@login_required
def natureza_operacao_create(request):
    if request.method == 'POST':
        form = NaturezaOperacaoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Natureza de Operação cadastrada com sucesso!')
            return redirect('fiscal:natureza_operacao_list')
    else:
        form = NaturezaOperacaoForm()
    
    context = {
        'form': form,
        'content_template': 'partials/fiscal/natureza_operacao_form.html',
        'data_page': 'natureza_operacao_create',
        'title': 'Cadastrar Natureza de Operação',
    }
    return render(request, 'base.html', context)

@login_required
def natureza_operacao_update(request, pk):
    natureza = get_object_or_404(NaturezaOperacao, pk=pk)
    if request.method == 'POST':
        form = NaturezaOperacaoForm(request.POST, instance=natureza)
        if form.is_valid():
            form.save()
            messages.success(request, 'Natureza de Operação atualizada com sucesso!')
            return redirect('fiscal:natureza_operacao_list')
    else:
        form = NaturezaOperacaoForm(instance=natureza)
    
    context = {
        'form': form,
        'content_template': 'partials/fiscal/natureza_operacao_form.html',
        'data_page': 'natureza_operacao_update',
        'title': 'Editar Natureza de Operação',
    }
    return render(request, 'base.html', context)

# --- Views para Importação de Excel ---

@login_required
def import_fiscal_data_view(request):
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        import_type = request.POST.get('import_type') # 'cfop' ou 'natureza_operacao'

        if not excel_file:
            messages.error(request, 'Nenhum arquivo Excel foi enviado.')
            return redirect('fiscal:import_fiscal_data')

        if not excel_file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, 'Formato de arquivo inválido. Por favor, envie um arquivo .xlsx ou .xls.')
            return redirect('fiscal:import_fiscal_data')

        try:
            workbook = openpyxl.load_workbook(excel_file)
            sheet = workbook.active
            
            # Pular o cabeçalho (primeira linha)
            rows = list(sheet.iter_rows(min_row=2, values_only=True))
            
            if import_type == 'cfop':
                with transaction.atomic():
                    for row_idx, row in enumerate(rows, start=2):
                        try:
                            codigo = str(row[0]).strip() if row[0] is not None else None
                            descricao = str(row[1]).strip() if row[1] is not None else None
                            categoria = str(row[2]).strip() if row[2] is not None else ''

                            if not codigo or not descricao:
                                messages.warning(request, f'Linha {row_idx}: Código ou Descrição do CFOP vazios. Ignorando linha.')
                                continue

                            Cfop.objects.update_or_create(
                                codigo=codigo,
                                defaults={'descricao': descricao, 'categoria': categoria}
                            )
                        except Exception as e:
                            messages.error(request, f'Erro ao processar CFOP na linha {row_idx}: {e}')
                            # Continua para a próxima linha, mas registra o erro
                messages.success(request, 'Importação de CFOPs concluída com sucesso!')
                return redirect('fiscal:cfop_list')

            elif import_type == 'natureza_operacao':
                with transaction.atomic():
                    for row_idx, row in enumerate(rows, start=2):
                        try:
                            codigo = str(row[0]).strip() if row[0] is not None else None
                            descricao = str(row[1]).strip() if row[1] is not None else None
                            observacoes = str(row[2]).strip() if row[2] is not None else ''

                            if not descricao:
                                messages.warning(request, f'Linha {row_idx}: Descrição da Natureza de Operação vazia. Ignorando linha.')
                                continue

                            NaturezaOperacao.objects.update_or_create(
                                descricao=descricao,
                                defaults={'codigo': codigo, 'observacoes': observacoes}
                            )
                        except Exception as e:
                            messages.error(request, f'Erro ao processar Natureza de Operação na linha {row_idx}: {e}')
                            # Continua para a próxima linha, mas registra o erro
                messages.success(request, 'Importação de Naturezas de Operação concluída com sucesso!')
                return redirect('fiscal:natureza_operacao_list')

            else:
                messages.error(request, 'Tipo de importação inválido.')

        except Exception as e:
            messages.error(request, f'Erro ao ler o arquivo Excel: {e}')

    context = {
        'content_template': 'partials/fiscal/import_fiscal_data.html',
        'data_page': 'import_fiscal_data',
        'title': 'Importar Dados Fiscais (Excel)',
    }
    return render(request, 'base.html', context)

@login_required
def download_fiscal_template_view(request):
    import_type = request.GET.get('type')
    
    if import_type == 'cfop':
        headers = ['codigo', 'descricao', 'categoria']
        filename = 'template_cfop.xlsx'
    elif import_type == 'natureza_operacao':
        headers = ['codigo', 'descricao', 'observacoes']
        filename = 'template_natureza_operacao.xlsx'
    else:
        messages.error(request, 'Tipo de template inválido.')
        return redirect('fiscal:import_fiscal_data')

    output = io.BytesIO()
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Dados Fiscais"

    # Escreve o cabeçalho
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
@csrf_exempt # Temporário para testes, remover em produção e usar CSRF token
def delete_fiscal_items(request):
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        item_type = data.get('item_type') # 'cfop' ou 'natureza_operacao'

        if not ids:
            return JsonResponse({'success': False, 'error': 'Nenhum ID fornecido para exclusão.'}, status=400)

        with transaction.atomic():
            if item_type == 'cfop':
                deleted_count, _ = Cfop.objects.filter(pk__in=ids).delete()
                model_name = "CFOP"
            elif item_type == 'natureza_operacao':
                deleted_count, _ = NaturezaOperacao.objects.filter(pk__in=ids).delete()
                model_name = "Natureza de Operação"
            else:
                return JsonResponse({'success': False, 'error': 'Tipo de item inválido.'}, status=400)

        return JsonResponse({'success': True, 'message': f'{deleted_count} {model_name}(s) excluído(s) com sucesso.'})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Requisição inválida.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
