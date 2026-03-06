from rest_framework import viewsets
from empresas.models import Empresa
from common.serializers.empresa import EmpresaSerializer
from django_filters.rest_framework import DjangoFilterBackend

class FornecedorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Empresa.objects.filter(fornecedor=True)
    serializer_class = EmpresaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tipo_empresa', 'status_empresa', 'cidade', 'uf']
