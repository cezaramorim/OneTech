# common/filters/produto.py

import django_filters
from produto.models import Produto

class ProdutoFilter(django_filters.FilterSet):
    # 🔍 Filtro por nome com busca parcial (case-insensitive)
    nome = django_filters.CharFilter(lookup_expr='icontains')

    # 🔍 Filtro por nome da categoria
    categoria = django_filters.CharFilter(field_name='categoria__nome', lookup_expr='icontains')

    # 🔍 Filtro por tipo (Produto, Insumo, Matéria-prima)
    tipo = django_filters.CharFilter(lookup_expr='exact')

    # ✅ Booleano: ativo ou inativo
    ativo = django_filters.BooleanFilter()

    # 🔢 Filtros por faixa de preço de venda
    preco_min = django_filters.NumberFilter(field_name='preco_venda', lookup_expr='gte')
    preco_max = django_filters.NumberFilter(field_name='preco_venda', lookup_expr='lte')

    # 📦 Estoque abaixo de X
    estoque_max = django_filters.NumberFilter(field_name='estoque_atual', lookup_expr='lte')

    # 🔍 Filtro por nome do fornecedor (razao_social ou nome_fantasia)
    fornecedor = django_filters.CharFilter(
        method='filter_fornecedor_razao_fantasia'
    )

    class Meta:
        model = Produto
        fields = ['nome', 'categoria', 'tipo', 'ativo']

    def filter_fornecedor_razao_fantasia(self, queryset, name, value):
        return queryset.filter(
            fornecedor__razao_social__icontains=value
        ) | queryset.filter(
            fornecedor__nome_fantasia__icontains=value
        )
