# relatorios/serializers.py

from rest_framework import serializers
from nota_fiscal.models import NotaFiscal

class NotaFiscalSerializer(serializers.ModelSerializer):
    """
    Serializador para NotaFiscal.
    - fornecedor: exibe apenas a razão social.
    - usuario: username de quem criou (campo created_by).
    - valor_total: alias para valor_total_nota.
    """
    fornecedor = serializers.CharField(
        source='fornecedor.razao_social',
        default='',
        read_only=True
    )
    usuario = serializers.SerializerMethodField()
    valor_total = serializers.DecimalField(
        source='valor_total_nota',
        max_digits=14,
        decimal_places=2,
        read_only=True
    )

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
        ]

    def get_usuario(self, obj):
        if obj.created_by:
            return obj.created_by.username
        return ''
