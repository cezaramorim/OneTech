from rest_framework import viewsets
from empresas.models import EmpresaAvancada
from common.serializers.empresa import EmpresaAvancadaCompletaSerializer
from django_filters.rest_framework import DjangoFilterBackend

class FornecedorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EmpresaAvancada.objects.filter(fornecedor=True)
    serializer_class = EmpresaAvancadaCompletaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tipo_empresa', 'status_empresa', 'cidade', 'uf']
