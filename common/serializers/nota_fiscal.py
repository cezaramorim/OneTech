from rest_framework import serializers
from nota_fiscal.models import NotaFiscal, TransporteNotaFiscal, DuplicataNotaFiscal, ItemNotaFiscal


class ItemNotaFiscalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemNotaFiscal
        fields = '__all__'


class NotaFiscalSerializer(serializers.ModelSerializer):
    fornecedor = serializers.CharField(
        source='fornecedor.razao_social',
        default='',
        read_only=True
    )
    usuario = serializers.SerializerMethodField()
    valor_total = serializers.DecimalField(
        source='valor_total_nota',
        max_digits=18,
        decimal_places=10,
        read_only=True
    )
    itens = ItemNotaFiscalSerializer(many=True, read_only=True) # Usando o serializer aninhado para itens

    class Meta:
        model = NotaFiscal
        fields = [
            'id',
            'numero',
            'fornecedor',
            'data_emissao',
            'data_saida',
            'valor_total',
            'usuario',
            'informacoes_adicionais',
            'valor_total_produtos',
            'valor_total_icms',
            'valor_total_pis',
            'valor_total_cofins',
            'valor_total_desconto',
            'itens',
        ]

    def get_usuario(self, obj):
        if obj.created_by:
            return obj.created_by.username
        return ''
