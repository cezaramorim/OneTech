from rest_framework import serializers
from .models import Tanque, TipoTanque, StatusTanque

from rest_framework import serializers
from .models import Tanque, TipoTanque, StatusTanque, Unidade, LinhaProducao, FaseProducao, Malha, TipoTela # Added imports

class TanqueSerializer(serializers.ModelSerializer):
    # Representa o campo metro_cubico como 'capacidade' para o frontend (read-only)
    capacidade = serializers.DecimalField(source='metro_cubico', max_digits=10, decimal_places=2, read_only=True)

    # Representa os ForeignKeys por seus IDs para o frontend
    tipo_tanque = serializers.PrimaryKeyRelatedField( # Changed to PrimaryKeyRelatedField
        queryset=TipoTanque.objects.all(),
        allow_null=True,
        required=False
    )
    status_tanque = serializers.PrimaryKeyRelatedField( # Changed to PrimaryKeyRelatedField
        queryset=StatusTanque.objects.all(),
        allow_null=True,
        required=False
    )
    unidade = serializers.PrimaryKeyRelatedField( # Changed to PrimaryKeyRelatedField
        queryset=Unidade.objects.all(),
        allow_null=True,
        required=False
    )
    linha_producao = serializers.PrimaryKeyRelatedField( # Changed to PrimaryKeyRelatedField
        queryset=LinhaProducao.objects.all(),
        allow_null=True,
        required=False
    )
    fase = serializers.PrimaryKeyRelatedField( # Changed to PrimaryKeyRelatedField
        queryset=FaseProducao.objects.all(),
        allow_null=True,
        required=False
    )
    malha = serializers.PrimaryKeyRelatedField( # Changed to PrimaryKeyRelatedField
        queryset=Malha.objects.all(),
        allow_null=True,
        required=False
    )
    tipo_tela = serializers.PrimaryKeyRelatedField( # Changed to PrimaryKeyRelatedField
        queryset=TipoTela.objects.all(),
        allow_null=True,
        required=False
    )

    class Meta:
        model = Tanque
        fields = [
            'id',
            'nome',
            'tag_tanque', 
            'sequencia',  
            'largura',
            'comprimento',
            'profundidade',
            'capacidade', # Mapeado para metro_cubico (read_only)
            'metro_quadrado', # Added
            'ha', # Added
            'tipo_tanque',
            'status_tanque',
            'unidade',
            'linha_producao',
            'fase',
            'malha',
            'tipo_tela',
            'ativo',
            'data_criacao',
        ]

