# relatorios/api.py
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

# Correção de caminhos absolutos após migração
from common.serializers.nota_fiscal import NotaFiscalSerializer
from common.filters.nota_fiscal import NotaFiscalFilter
from nota_fiscal.models import NotaFiscal

class NotaFiscalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint que lista as Notas Fiscais salvas.
    GET /relatorios/api/v1/notas-entradas/
    Permite filtros via query params:
      ?numero=&amp;fornecedor=&amp;emissao_de=&amp;emissao_ate=&amp;entrada_de=&amp;entrada_ate=
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotaFiscalSerializer
    queryset = (
        NotaFiscal.objects
        .select_related('fornecedor', 'created_by')
        .order_by('-data_emissao')
    )

    # Filtro, busca e ordenação
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = NotaFiscalFilter
    search_fields = ['numero', 'fornecedor__razao_social']
    ordering_fields = ['data_emissao', 'valor_total_nota']