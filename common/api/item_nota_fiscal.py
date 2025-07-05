from rest_framework import viewsets
from nota_fiscal.models import ItemNotaFiscal
from common.serializers.nota_fiscal import ItemNotaFiscalSerializer

class ItemNotaFiscalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ItemNotaFiscal.objects.all()
    serializer_class = ItemNotaFiscalSerializer
