# common/api/produto.py
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from produto.models import Produto
from common.serializers.produto import ProdutoSerializer
from common.filters.produto import ProdutoFilter

class ProdutoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProdutoFilter
