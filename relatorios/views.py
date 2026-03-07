# relatorios/views.py

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_http_methods
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from nota_fiscal.models import NotaFiscal, TransporteNotaFiscal, DuplicataNotaFiscal, ItemNotaFiscal
from relatorios.forms import NotaFiscalForm
from common.serializers.nota_fiscal import NotaFiscalSerializer
from decimal import Decimal
from produto.models_entradas import EntradaProduto

from common.utils import formatters

valor = formatters.formatar_moeda_br("1234.56")

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_notas_entradas(request):
    """
    API endpoint REST (JSON) para listar todas as Notas Fiscais:
      - URL: GET /relatorios/api/v1/notas-entradas/
      - Requer autenticação (token/session).
      - Retorna: numero, fornecedor, data_emissao, data_saida, valor_total_nota, usuario.
    """
    qs = NotaFiscal.objects.select_related('fornecedor', 'created_by').all()
    serializer = NotaFiscalSerializer(qs, many=True, context={'request': request})
    return Response(serializer.data)


@login_required
@require_GET
def notas_entradas_view(request):
    """
    View HTML para listagem de Notas:
      - GET normal: renderiza 'relatorios/notas_entradas.html' (página completa).
      - AJAX (XHR): renderiza apenas 'partials/relatorios/notas_entradas.html'.
    """
    qs = NotaFiscal.objects.select_related('fornecedor', 'created_by').all()
    context = {'entradas': qs}

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    tpl = 'partials/relatorios/notas_entradas.html' if is_ajax else 'relatorios/notas_entradas.html'
    return render(request, tpl, context)


@login_required
@require_http_methods(['GET', 'POST'])
def editar_entrada_view(request, pk):
    nota = get_object_or_404(NotaFiscal, pk=pk)

    if request.method == 'POST':
        form = NotaFiscalForm(request.POST, instance=nota)
        if form.is_valid():
            form.save()
            return JsonResponse({'mensagem': 'Entrada atualizada com sucesso.'})
        return JsonResponse({'erros': form.errors}, status=400)

    form = NotaFiscalForm(instance=nota)
    produtos = nota.itens.all()
    transporte = getattr(nota, 'transporte', None)
    duplicatas = nota.duplicatas.all()
    for d in duplicatas:
        if d.valor:
            d.valor = Decimal(d.valor) / Decimal('100')  # Corrige centavos -> reais


    return render(request, 'partials/relatorios/editar_entrada.html', {
        'form': form,
        'nota': nota,
        'produtos': produtos,
        'transporte': transporte,
        'duplicatas': duplicatas,
        'data_page': 'editar-entrada',  # Adicionado
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_nota_detalhada(request, pk):
    """
    Retorna os dados completos da Nota Fiscal para preencher a tela de edição.
    """
    try:
        nota = NotaFiscal.objects.prefetch_related('itens__produto').get(pk=pk)
    except NotaFiscal.DoesNotExist:
        return Response({"erro": "Nota não encontrada"}, status=404)

    # Dados principais da nota
    nota_data = {
        "id": nota.id,
        "numero": nota.numero,
        "fornecedor": nota.fornecedor.id if nota.fornecedor else None,
        "data_emissao": nota.data_emissao,
        "data_saida": nota.data_saida,
        "valor_total_produtos": nota.valor_total_produtos,
        "valor_total_nota": nota.valor_total_nota,
        "valor_total_icms": nota.valor_total_icms,
        "valor_total_pis": nota.valor_total_pis,
        "valor_total_cofins": nota.valor_total_cofins,
        "valor_total_desconto": nota.valor_total_desconto,
        "informacoes_adicionais": nota.informacoes_adicionais,
    }

    # Produtos da nota
    produtos_data = []
    for item in nota.itens.all():
        # Calcula o valor do ICMS para o item
        valor_icms = Decimal('0')
        if item.base_calculo_icms and item.aliquota_icms:
            valor_icms = item.base_calculo_icms * (item.aliquota_icms / Decimal('100'))

        # Calcula o valor do IPI para o item
        valor_ipi = Decimal('0')
        if hasattr(item, 'base_calculo_ipi') and hasattr(item, 'aliquota_ipi') and item.base_calculo_ipi and item.aliquota_ipi:
            valor_ipi = item.base_calculo_ipi * (item.aliquota_ipi / Decimal('100'))

        produto_data = {
            "codigo_interno": item.produto.codigo_interno if item.produto else None,
            "codigo_fornecedor": item.produto.codigo_fornecedor if item.produto else item.codigo,
            "descricao": item.descricao,
            "ncm": item.ncm,
            "cfop": item.cfop,
            "quantidade": item.quantidade,
            "unidade": item.unidade,
            "valor_unitario": item.valor_unitario,
            "valor_total": item.valor_total,
            "icms": valor_icms,
            "ipi": valor_ipi,
            "desconto": item.desconto or 0,
        }
        produtos_data.append(produto_data)


    # Transporte da nota
    try:
        transporte = TransporteNotaFiscal.objects.get(nota_fiscal=nota)
        transporte_data = {
            "modalidade_frete": transporte.modalidade_frete,
            "transportadora_nome": transporte.transportadora_nome,
            "transportadora_cnpj": transporte.transportadora_cnpj,
            "veiculo_placa": transporte.placa_veiculo,
            "veiculo_uf": transporte.uf_veiculo,
            "veiculo_rntc": transporte.rntc,
            "quantidade_volumes": transporte.quantidade_volumes,
            "especie_volumes": transporte.especie_volumes,
            "peso_liquido": transporte.peso_liquido,
            "peso_bruto": transporte.peso_bruto,
        }
    except TransporteNotaFiscal.DoesNotExist:
        transporte_data = {}

    # Duplicatas
    duplicatas = DuplicataNotaFiscal.objects.filter(nota_fiscal=nota)
    duplicatas_data = [
        {
            "numero": d.numero,
            "valor": d.valor,
            "vencimento": d.vencimento
        }
        for d in duplicatas
    ]

    return Response({
        "nota": nota_data,
        "produtos": produtos_data,
        "transporte": transporte_data,
        "duplicatas": duplicatas_data
    })

# relatorios/views.py
@login_required
def relatorio_nota_fiscal_view(request):
    """
    Exibe a tela de relatório de notas fiscais com filtros (cliente, data, etc.).
    A tabela é carregada via API.
    """
    return render(request, 'partials/relatorios/relatorio_nota_fiscal.html')

from producao.models import (
    Tanque,
    LinhaProducao,
    StatusTanque,
    Unidade,
    FaseProducao,
    TipoTanque,
    Malha,
    TipoTela,
)
from empresas.models import Empresa, CategoriaEmpresa
from django.db.models import Q
from django.urls import reverse
import csv


def _empty(value):
    return '' if value is None else str(value)


def _fmt_date(value):
    return value.strftime('%d/%m/%Y') if value else ''


def _fmt_datetime(value):
    return value.strftime('%d/%m/%Y %H:%M:%S') if value else ''


def _mask_document(value):
    digits = ''.join(ch for ch in str(value or '') if ch.isdigit())
    if len(digits) == 14:
        return f'{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}'
    if len(digits) == 11:
        return f'{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}'
    return _empty(value)


def _excel_safe(value):
    text = '' if value is None else str(value)
    if text[:1] in ('=', '+', '-', '@'):
        return "'" + text
    return text


def _build_report_data(report_type, params):
    """Monta metadados e linhas do relatorio solicitado."""
    report_type = (report_type or '').strip()

    if report_type == 'tanques':
        qs = Tanque.objects.select_related(
            'linha_producao', 'fase', 'status_tanque', 'tipo_tanque', 'unidade', 'malha', 'tipo_tela'
        ).all().order_by('nome', 'id')

        nome = (params.get('tanque_nome') or '').strip()
        tag_tanque = (params.get('tag_tanque') or '').strip()
        data_cadastro_inicial = (params.get('data_cadastro_inicial') or '').strip()
        data_cadastro_final = (params.get('data_cadastro_final') or '').strip()

        linha_id = (params.get('linha_producao_id') or '').strip()
        unidade_id = (params.get('unidade_id') or '').strip()
        fase_id = (params.get('fase_id') or '').strip()
        tipo_tanque_id = (params.get('tipo_tanque_id') or '').strip()
        malha_id = (params.get('malha_id') or '').strip()
        tipo_tela_id = (params.get('tipo_tela_id') or '').strip()
        status_id = (params.get('status_tanque_id') or '').strip()
        ativo = (params.get('ativo') or '').strip().lower()

        if nome:
            qs = qs.filter(nome__icontains=nome)
        if tag_tanque:
            qs = qs.filter(tag_tanque__icontains=tag_tanque)
        if data_cadastro_inicial:
            qs = qs.filter(data_criacao__date__gte=data_cadastro_inicial)
        if data_cadastro_final:
            qs = qs.filter(data_criacao__date__lte=data_cadastro_final)
        if linha_id.isdigit():
            qs = qs.filter(linha_producao_id=int(linha_id))
        if unidade_id.isdigit():
            qs = qs.filter(unidade_id=int(unidade_id))
        if fase_id.isdigit():
            qs = qs.filter(fase_id=int(fase_id))
        if tipo_tanque_id.isdigit():
            qs = qs.filter(tipo_tanque_id=int(tipo_tanque_id))
        if malha_id.isdigit():
            qs = qs.filter(malha_id=int(malha_id))
        if tipo_tela_id.isdigit():
            qs = qs.filter(tipo_tela_id=int(tipo_tela_id))
        if status_id.isdigit():
            qs = qs.filter(status_tanque_id=int(status_id))
        if ativo in {'sim', 'nao'}:
            qs = qs.filter(ativo=(ativo == 'sim'))

        columns = [
            ('id', 'ID'),
            ('nome', 'Nome'),
            ('largura', 'Largura'),
            ('comprimento', 'Comprimento'),
            ('profundidade', 'Profundidade'),
            ('metro_quadrado', 'Metro Quadrado'),
            ('metro_cubico', 'Metro Cubico'),
            ('ha', 'HA'),
            ('unidade', 'Unidade'),
            ('fase', 'Fase'),
            ('tipo_tanque', 'Tipo Tanque'),
            ('linha_producao', 'Linha Producao'),
            ('malha', 'Malha'),
            ('status_tanque', 'Status Tanque'),
            ('tipo_tela', 'Tipo Tela'),
            ('sequencia', 'Sequencia'),
            ('tag_tanque', 'Tag Tanque'),
            ('ativo', 'Ativo'),
            ('data_criacao', 'Data Criacao'),
        ]

        rows = []
        for t in qs:
            rows.append({
                'id': t.id,
                'nome': _empty(t.nome),
                'largura': _empty(t.largura),
                'comprimento': _empty(t.comprimento),
                'profundidade': _empty(t.profundidade),
                'metro_quadrado': _empty(t.metro_quadrado),
                'metro_cubico': _empty(t.metro_cubico),
                'ha': _empty(t.ha),
                'unidade': _empty(t.unidade.nome if t.unidade else ''),
                'fase': _empty(t.fase.nome if t.fase else ''),
                'tipo_tanque': _empty(t.tipo_tanque.nome if t.tipo_tanque else ''),
                'linha_producao': _empty(t.linha_producao.nome if t.linha_producao else ''),
                'malha': _empty(t.malha.nome if t.malha else ''),
                'status_tanque': _empty(t.status_tanque.nome if t.status_tanque else ''),
                'tipo_tela': _empty(t.tipo_tela.nome if t.tipo_tela else ''),
                'sequencia': _empty(t.sequencia),
                'tag_tanque': _empty(t.tag_tanque),
                'ativo': 'Sim' if t.ativo else 'Nao',
                'data_criacao': _fmt_datetime(t.data_criacao),
            })

        return {
            'key': 'tanques',
            'title': 'Cadastro de Tanques',
            'columns': columns,
            'rows': rows,
        }

    if report_type == 'empresas':
        qs = Empresa.objects.select_related('categoria', 'vendedor').all().order_by('razao_social', 'nome_fantasia', 'nome', 'id')

        termo = (params.get('empresa_nome') or '').strip()
        data_cadastro_inicial = (params.get('data_cadastro_inicial') or '').strip()
        data_cadastro_final = (params.get('data_cadastro_final') or '').strip()
        tipo_empresa = (params.get('tipo_empresa') or '').strip().lower()
        status_empresa = (params.get('status_empresa') or '').strip().lower()
        categoria_id = (params.get('categoria_id') or '').strip()
        cidade = (params.get('cidade') or '').strip()
        uf = (params.get('uf') or '').strip().upper()
        cliente = (params.get('cliente') or '').strip().lower()
        fornecedor = (params.get('fornecedor') or '').strip().lower()

        if termo:
            qs = qs.filter(
                Q(razao_social__icontains=termo)
                | Q(nome_fantasia__icontains=termo)
                | Q(nome__icontains=termo)
                | Q(cnpj__icontains=termo)
                | Q(cpf__icontains=termo)
            )
        if data_cadastro_inicial:
            qs = qs.filter(data_cadastro__gte=data_cadastro_inicial)
        if data_cadastro_final:
            qs = qs.filter(data_cadastro__lte=data_cadastro_final)
        if tipo_empresa in {'pj', 'pf'}:
            qs = qs.filter(tipo_empresa=tipo_empresa)
        if status_empresa in {'ativa', 'inativa'}:
            qs = qs.filter(status_empresa=status_empresa)
        if categoria_id.isdigit():
            qs = qs.filter(categoria_id=int(categoria_id))
        if cidade:
            qs = qs.filter(cidade__icontains=cidade)
        if uf:
            qs = qs.filter(uf__iexact=uf)
        if cliente in {'sim', 'nao'}:
            qs = qs.filter(cliente=(cliente == 'sim'))
        if fornecedor in {'sim', 'nao'}:
            qs = qs.filter(fornecedor=(fornecedor == 'sim'))

        columns = [
            ('id', 'ID'),
            ('tipo_empresa', 'Tipo Empresa'),
            ('razao_social', 'Razao Social'),
            ('nome_fantasia', 'Nome Fantasia'),
            ('cnpj', 'CNPJ'),
            ('ie', 'Inscricao Estadual'),
            ('regime_tributario', 'Regime Tributario'),
            ('contribuinte_icms', 'Contribuinte ICMS'),
            ('inscricao_municipal', 'Inscricao Municipal'),
            ('nome', 'Nome'),
            ('cpf', 'CPF'),
            ('rg', 'RG'),
            ('profissao', 'Profissao'),
            ('cnae_principal', 'CNAE Principal'),
            ('cnae_secundario', 'CNAE Secundario'),
            ('data_abertura', 'Data Abertura'),
            ('data_cadastro', 'Data Cadastro'),
            ('cep', 'CEP'),
            ('logradouro', 'Logradouro'),
            ('numero', 'Numero'),
            ('complemento', 'Complemento'),
            ('bairro', 'Bairro'),
            ('cidade', 'Cidade'),
            ('uf', 'UF'),
            ('telefone', 'Telefone'),
            ('celular', 'Celular'),
            ('whatsapp', 'WhatsApp'),
            ('email', 'Email'),
            ('site', 'Site'),
            ('contato_financeiro_nome', 'Contato Financeiro Nome'),
            ('contato_financeiro_email', 'Contato Financeiro Email'),
            ('contato_financeiro_telefone', 'Contato Financeiro Telefone'),
            ('contato_financeiro_celular', 'Contato Financeiro Celular'),
            ('contato_comercial_nome', 'Contato Comercial Nome'),
            ('contato_comercial_email', 'Contato Comercial Email'),
            ('contato_comercial_telefone', 'Contato Comercial Telefone'),
            ('contato_comercial_celular', 'Contato Comercial Celular'),
            ('condicao_pagamento', 'Condicao Pagamento'),
            ('comissao', 'Comissao'),
            ('observacoes', 'Observacoes'),
            ('vendedor', 'Vendedor'),
            ('cliente', 'Cliente'),
            ('fornecedor', 'Fornecedor'),
            ('status_empresa', 'Status Empresa'),
            ('categoria', 'Categoria'),
        ]

        rows = []
        for e in qs:
            rows.append({
                'id': e.id,
                'tipo_empresa': 'Pessoa Juridica' if e.tipo_empresa == 'pj' else 'Pessoa Fisica',
                'razao_social': _empty(e.razao_social),
                'nome_fantasia': _empty(e.nome_fantasia),
                'cnpj': _mask_document(e.cnpj),
                'ie': _empty(e.ie),
                'regime_tributario': _empty(e.regime_tributario),
                'contribuinte_icms': 'Sim' if e.contribuinte_icms else 'Nao',
                'inscricao_municipal': _empty(e.inscricao_municipal),
                'nome': _empty(e.nome),
                'cpf': _mask_document(e.cpf),
                'rg': _empty(e.rg),
                'profissao': _empty(e.profissao),
                'cnae_principal': _empty(e.cnae_principal),
                'cnae_secundario': _empty(e.cnae_secundario),
                'data_abertura': _fmt_date(e.data_abertura),
                'data_cadastro': _fmt_date(e.data_cadastro),
                'cep': _empty(e.cep),
                'logradouro': _empty(e.logradouro),
                'numero': _empty(e.numero),
                'complemento': _empty(e.complemento),
                'bairro': _empty(e.bairro),
                'cidade': _empty(e.cidade),
                'uf': _empty(e.uf),
                'telefone': _empty(e.telefone),
                'celular': _empty(e.celular),
                'whatsapp': _empty(e.whatsapp),
                'email': _empty(e.email),
                'site': _empty(e.site),
                'contato_financeiro_nome': _empty(e.contato_financeiro_nome),
                'contato_financeiro_email': _empty(e.contato_financeiro_email),
                'contato_financeiro_telefone': _empty(e.contato_financeiro_telefone),
                'contato_financeiro_celular': _empty(e.contato_financeiro_celular),
                'contato_comercial_nome': _empty(e.contato_comercial_nome),
                'contato_comercial_email': _empty(e.contato_comercial_email),
                'contato_comercial_telefone': _empty(e.contato_comercial_telefone),
                'contato_comercial_celular': _empty(e.contato_comercial_celular),
                'condicao_pagamento': _empty(e.condicao_pagamento),
                'comissao': _empty(e.comissao),
                'observacoes': _empty(e.observacoes),
                'vendedor': _empty(getattr(e.vendedor, 'nome_completo', '') or getattr(e.vendedor, 'username', '') if e.vendedor else ''),
                'cliente': 'Sim' if e.cliente else 'Nao',
                'fornecedor': 'Sim' if e.fornecedor else 'Nao',
                'status_empresa': _empty(e.status_empresa).capitalize(),
                'categoria': _empty(e.categoria.nome if e.categoria else ''),
            })

        return {
            'key': 'empresas',
            'title': 'Cadastro de Empresas',
            'columns': columns,
            'rows': rows,
        }

    return {
        'key': 'indefinido',
        'title': 'Relatorio nao identificado',
        'columns': [],
        'rows': [],
    }


@login_required
def impressao_relatorios_view(request):
    """Tela principal de impressao de relatorios (layout com menu lateral)."""
    context = {
        'data_page': 'impressao-relatorios',
        'linhas_producao': LinhaProducao.objects.all().order_by('nome'),
        'unidades': Unidade.objects.all().order_by('nome'),
        'fases_producao': FaseProducao.objects.all().order_by('nome'),
        'tipos_tanque': TipoTanque.objects.all().order_by('nome'),
        'malhas': Malha.objects.all().order_by('nome'),
        'tipos_tela': TipoTela.objects.all().order_by('nome'),
        'status_tanques': StatusTanque.objects.all().order_by('nome'),
        'categorias_empresas': CategoriaEmpresa.objects.all().order_by('nome'),
    }

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        return render(request, 'partials/relatorios/impressao_relatorios.html', context)

    context['content_template'] = 'partials/relatorios/impressao_relatorios.html'
    return render(request, 'base.html', context)


@login_required
@require_GET
def impressao_relatorios_preview_view(request):
    """Pre-visualizacao do relatorio em nova janela com layout completo do projeto."""
    report_type = request.GET.get('report_type', '')
    report = _build_report_data(report_type, request.GET)

    query_params = request.GET.copy()
    download_url = request.build_absolute_uri(
        f"{reverse('relatorios:impressao_relatorios_download_csv')}?{query_params.urlencode()}"
    )

    columns = report.get('columns', [])
    matrix = [[row.get(key, '') for key, _ in columns] for row in report.get('rows', [])]

    context = {
        'data_page': 'impressao-relatorios-preview',
        'report': report,
        'matrix': matrix,
        'download_url': download_url,
    }
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        return render(request, 'partials/relatorios/impressao_relatorios_preview.html', context)

    context['content_template'] = 'partials/relatorios/impressao_relatorios_preview.html'
    return render(request, 'base.html', context)


@login_required
@require_GET
def impressao_relatorios_download_csv_view(request):
    """Download CSV do relatorio solicitado."""
    report_type = request.GET.get('report_type', '')
    report = _build_report_data(report_type, request.GET)

    safe_key = report.get('key') or 'relatorio'
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{safe_key}.csv"'

    response.write('ï»¿')
    writer = csv.writer(response, delimiter=';')

    columns = report.get('columns', [])
    writer.writerow([label for _, label in columns])
    for row in report.get('rows', []):
        writer.writerow([_excel_safe(row.get(key, '')) for key, _ in columns])

    return response
