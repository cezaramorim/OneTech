from django.db.models import Case, IntegerField, Q, Value, When
from rest_framework import serializers, viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import DjangoModelPermissions

from fiscal.models import Cfop, NaturezaOperacao


class CfopSerializer(serializers.ModelSerializer):
    text = serializers.SerializerMethodField()

    def get_text(self, obj):
        descricao = (obj.descricao or '').strip()
        if descricao:
            return f'{obj.codigo} - {descricao}'
        return obj.codigo

    class Meta:
        model = Cfop
        fields = ['codigo', 'descricao', 'categoria', 'text']


class NaturezaOperacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = NaturezaOperacao
        fields = ['codigo', 'descricao', 'observacoes']


class CfopPagination(LimitOffsetPagination):
    default_limit = 50
    max_limit = 50


class CfopViewSet(viewsets.ModelViewSet):
    queryset = Cfop.objects.only('codigo', 'descricao', 'categoria').order_by('codigo')
    serializer_class = CfopSerializer
    pagination_class = CfopPagination
    permission_classes = [DjangoModelPermissions]
    lookup_field = 'codigo'  # Permite buscar CFOPs pelo codigo
    filter_backends = []

    def get_queryset(self):
        queryset = Cfop.objects.only('codigo', 'descricao', 'categoria')
        params = getattr(self.request, 'query_params', self.request.GET)
        term = (params.get('search') or '').strip()
        if not term:
            return queryset.order_by('codigo')

        return (
            queryset.filter(
                Q(codigo__icontains=term)
                | Q(descricao__icontains=term)
                | Q(categoria__icontains=term)
            )
            .annotate(
                match_priority=Case(
                    When(descricao__istartswith=term, then=Value(0)),
                    When(categoria__istartswith=term, then=Value(1)),
                    When(codigo__istartswith=term, then=Value(2)),
                    default=Value(3),
                    output_field=IntegerField(),
                )
            )
            .order_by('match_priority', 'codigo')
        )


class NaturezaOperacaoViewSet(viewsets.ModelViewSet):
    queryset = NaturezaOperacao.objects.all()
    serializer_class = NaturezaOperacaoSerializer
    permission_classes = [DjangoModelPermissions]
    lookup_field = 'codigo'  # Permite buscar Naturezas de Operacao pelo codigo
