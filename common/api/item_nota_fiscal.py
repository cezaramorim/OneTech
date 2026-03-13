from rest_framework import viewsets
from common.api.permissions import DjangoModelPermissionsWithView
from nota_fiscal.models import ItemNotaFiscal
from common.serializers.nota_fiscal import ItemNotaFiscalSerializer

class ItemNotaFiscalViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [DjangoModelPermissionsWithView]
    queryset = ItemNotaFiscal.objects.all()
    serializer_class = ItemNotaFiscalSerializer
