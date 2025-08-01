import io
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from common.messages_utils import get_app_messages
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

from .models import Cfop, NaturezaOperacao
from .forms import CfopForm, NaturezaOperacaoForm, UploadExcelForm

# Certifique-se de ter o openpyxl instalado: pip install openpyxl
import openpyxl

# --- Views para CFOP ---

@login_required
def cfop_list(request):
    ordenacao = request.GET.get('ordenacao', 'codigo') # Padrão: ordenar por código
    termo_busca = request.GET.get('busca', '').strip()

    # Valida o campo de ordenação para prevenir injeção de SQL ou erros inesperados.
    # Se o campo não for válido, a ordenação padrão é usada.
    valid_sort_fields = ['codigo', 'descricao', 'categoria']
    if ordenacao.startswith('-'):
        field = ordenacao[1:]
    else:
        field = ordenacao

    if field not in valid_sort_fields:
        ordenacao = 'codigo' # Volta para o padrão se o campo for inválido

    cfops = Cfop.objects.all()

    if termo_busca:
        # Aplica filtro de busca usando Q objects para buscar em múltiplos campos.
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
    app_messages = get_app_messages(request)
    if request.method == 'POST':
        form = CfopForm(request.POST)
        if form.is_valid():
            form.save()
            app_messages.success_created(form.instance)
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

    # Valida o campo de ordenação para prevenir injeção de SQL ou erros inesperados.
    # Se o campo não for válido, a ordenação padrão é usada.
    valid_sort_fields = ['codigo', 'descricao', 'observacoes']
    if ordenacao.startswith('-'):
        field = ordenacao[1:]
    else:
        field = ordenacao

    if field not in valid_sort_fields:
        ordenacao = 'descricao' # Volta para o padrão se o campo for inválido

    naturezas = NaturezaOperacao.objects.all()

    if termo_busca:
        # Aplica filtro de busca usando Q objects para buscar em múltiplos campos.
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
    app_messages = get_app_messages(request)
    if request.method == 'POST':
        form = NaturezaOperacaoForm(request.POST)
        if form.is_valid():
            form.save()
            app_messages.success_created(form.instance)
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
    
    context = {
        'form': form,
        'content_template': 'partials/fiscal/natureza_operacao_form.html',
        'data_page': 'natureza_operacao_update',
        'title': 'Editar Natureza de Operação',
    }
    return render(request, 'base.html', context)

# --- Views para Importação de Excel ---

from .utils import import_cfop_from_excel, import_natureza_operacao_from_excel

@login_required
@permission_required('fiscal.add_cfop', raise_exception=True)
def import_fiscal_data_view(request):
    app_messages = get_app_messages(request)
    """
    View para importar dados fiscais (CFOPs ou Naturezas de Operação) a partir de um arquivo Excel.

    Requer que o usuário esteja autenticado e tenha a permissão 'fiscal.add_cfop'.

    GET: Exibe o formulário de upload.
    POST: Processa o arquivo Excel enviado, importa os dados e redireciona para a lista correspondente.
    """
    if request.method == 'POST':
        form = UploadExcelForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = form.cleaned_data['excel_file']
            import_type = form.cleaned_data['import_type']

            if import_type == 'cfop':
                result = import_cfop_from_excel(excel_file)
                redirect_url = 'fiscal:cfop_list'
            elif import_type == 'natureza_operacao':
                result = import_natureza_operacao_from_excel(excel_file)
                redirect_url = 'fiscal:natureza_operacao_list'
            
            if result["success"]:
                app_messages.success_imported(instance=None, custom_message=result["message"])
            else:
                app_messages.error(result["message"])
            
            return redirect(redirect_url)
        else:
            # Se o formulário não for válido, renderiza a página com os erros
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"Campo '{field}': {error}")
            app_messages.error("Erro no formulário de importação: " + "; ".join(error_messages))
            
            context = {
                'form': form,
                'content_template': 'partials/fiscal/import_fiscal_data.html',
                'data_page': 'import_fiscal_data',
                'title': 'Importar Dados Fiscais (Excel)',
            }
            return render(request, 'base.html', context)

    else:
        form = UploadExcelForm()

    context = {
        'form': form,
        'content_template': 'partials/fiscal/import_fiscal_data.html',
        'data_page': 'import_fiscal_data',
        'title': 'Importar Dados Fiscais (Excel)',
    }
    return render(request, 'base.html', context)

@login_required
def download_fiscal_template_view(request):
    app_messages = get_app_messages(request)
    import_type = request.GET.get('type')
    
    if import_type == 'cfop':
        headers = ['codigo', 'descricao', 'categoria']
        filename = 'template_cfop.xlsx'
    elif import_type == 'natureza_operacao':
        headers = ['codigo', 'descricao', 'observacoes']
        filename = 'template_natureza_operacao.xlsx'
    else:
        app_messages.error('Tipo de template inválido.')
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
    app_messages = get_app_messages(request)
    """
    View para exclusão de itens fiscais (CFOPs ou Naturezas de Operação) via requisição AJAX.
    Espera um JSON com 'ids' (lista de IDs a serem excluídos) e 'item_type' ('cfop' ou 'natureza_operacao').
    """
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        item_type = data.get('item_type')

        if not ids:
            message = app_messages.error('Nenhum ID fornecido para exclusão.')
            return JsonResponse({'success': False, 'message': message}, status=400)

        with transaction.atomic():
            if item_type == 'cfop':
                model = Cfop
                model_name = "CFOP"
            elif item_type == 'natureza_operacao':
                model = NaturezaOperacao
                model_name = "Natureza de Operação"
            else:
                message = app_messages.error('Tipo de item inválido.')
                return JsonResponse({'success': False, 'message': message}, status=400)
            
            deleted_count, _ = model.objects.filter(pk__in=ids).delete()

        message = app_messages.success_deleted(model_name, f'{deleted_count} selecionado(s)')
        return JsonResponse({'success': True, 'message': message})

    except json.JSONDecodeError:
        message = app_messages.error('Requisição inválida. JSON malformado.')
        return JsonResponse({'success': False, 'message': message}, status=400)
    except Exception as e:
        message = app_messages.error(f'Erro ao excluir itens fiscais: {str(e)}')
        return JsonResponse({'success': False, 'message': message}, status=500)
