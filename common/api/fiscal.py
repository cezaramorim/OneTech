from rest_framework import serializers, viewsets
from fiscal.models import Cfop, NaturezaOperacao

class CfopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cfop
        fields = ['codigo', 'descricao', 'categoria']

class NaturezaOperacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = NaturezaOperacao
        fields = ['codigo', 'descricao', 'observacoes']

class CfopViewSet(viewsets.ModelViewSet):
    queryset = Cfop.objects.all()
    serializer_class = CfopSerializer
    lookup_field = 'codigo' # Permite buscar CFOPs pelo código

class NaturezaOperacaoViewSet(viewsets.ModelViewSet):
    queryset = NaturezaOperacao.objects.all()
    serializer_class = NaturezaOperacaoSerializer
    lookup_field = 'codigo' # Permite buscar Naturezas de Operação pelo código
