# relatorios/views.py

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_http_methods
from django.contrib.auth.decorators import login_required

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from nota_fiscal.models import NotaFiscal
from relatorios.forms import NotaFiscalForm
from relatorios.serializers import NotaFiscalSerializer


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
    """
    GET  → renderiza o formulário de edição da NotaFiscal (partial).
    POST → processa o form, salva e retorna JSON {mensagem} ou {erros}.
    """
    nota = get_object_or_404(NotaFiscal, pk=pk)

    if request.method == 'POST':
        form = NotaFiscalForm(request.POST, instance=nota)
        if form.is_valid():
            form.save()
            return JsonResponse({'mensagem': 'Entrada atualizada com sucesso.'})
        return JsonResponse({'erros': form.errors}, status=400)

    form = NotaFiscalForm(instance=nota)
    return render(request,
                  'partials/relatorios/editar_entrada.html',
                  {'form': form, 'nota': nota})
