# nota_fiscal/api.py
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

# Correção de caminhos absolutos após migração
from common.serializers.nota_fiscal import NotaFiscalSerializer
from common.filters.nota_fiscal import NotaFiscalFilter
from nota_fiscal.models import NotaFiscal
# Função de parsing e conversão de XML para JSON
from nota_fiscal.utils import importar_nfe_e_retornar_json


class NotaFiscalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint que lista as Notas Fiscais salvas.
    GET /api/v1/notas-entradas/
    Permite filtros via query params:
      ?numero=&fornecedor=&emissao_de=&emissao_ate=&entrada_de=&entrada_ate=
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

    @action(detail=False, methods=['post'], url_path='importar-nfe')
    def importar_nfe(self, request):
        """
        Recebe um arquivo XML via multipart/form-data em 'xml',
        executa o parsing e retorna o JSON resultante.
        """
        xml_file = request.FILES.get('xml')
        if not xml_file:
            return Response({'erro': 'Nenhum arquivo XML enviado.'}, status=400)

        try:
            resultado = importar_nfe_e_retornar_json(xml_file)
        except Exception as e:
            return Response({'erro': str(e)}, status=500)

        return Response(resultado)
