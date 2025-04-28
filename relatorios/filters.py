# relatorios/filters.py
import django_filters
from nota_fiscal.models import NotaFiscal

class NotaFiscalFilter(django_filters.FilterSet):
    numero = django_filters.CharFilter(
        field_name='numero', lookup_expr='icontains', label='Número')
    fornecedor = django_filters.CharFilter(
        field_name='fornecedor__razao_social', lookup_expr='icontains', label='Fornecedor')
    emissao_de = django_filters.DateFilter(
        field_name='data_emissao', lookup_expr='gte', label='Emissão (de)')
    emissao_ate = django_filters.DateFilter(
        field_name='data_emissao', lookup_expr='lte', label='Emissão (até)')
    entrada_de = django_filters.DateFilter(
        field_name='data_saida', lookup_expr='gte', label='Entrada (de)')
    entrada_ate = django_filters.DateFilter(
        field_name='data_saida', lookup_expr='lte', label='Entrada (até)')

    class Meta:
        model = NotaFiscal
        fields = [
            'numero', 'fornecedor',
            'emissao_de', 'emissao_ate',
            'entrada_de', 'entrada_ate',
        ]