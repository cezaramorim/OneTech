# relatorios/views.py

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_http_methods
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from nota_fiscal.models import NotaFiscal, TransporteNotaFiscal, DuplicataNotaFiscal
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
            d.valor = Decimal(d.valor) / Decimal('100')  # Corrige centavos → reais


    return render(request, 'partials/relatorios/editar_entrada.html', {
        'form': form,
        'nota': nota,
        'produtos': produtos,
        'transporte': transporte,
        'duplicatas': duplicatas,
        'data_page': 'editar-entrada',  # ✅ Adicionado
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_nota_detalhada(request, pk):
    """
    Retorna os dados completos da Nota Fiscal para preencher a tela de edição.
    """
    try:
        nota = NotaFiscal.objects.get(pk=pk)
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
    produtos = EntradaProduto.objects.filter(numero_nota=nota.numero)
    produtos_data = [
        {
            "codigo": p.produto.codigo,
            "descricao": p.produto.nome,
            "ncm": p.produto.ncm,
            "cfop": p.produto.cfop,
            "quantidade": p.quantidade,
            "unidade": p.produto.unidade_comercial,
            "valor_unitario": p.preco_unitario,
            "valor_total": p.preco_total,
            "icms": p.icms_valor,
            "ipi": p.ipi_valor,
            "desconto": 0,  # ajuste conforme necessidade
        }
        for p in produtos
    ]

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
