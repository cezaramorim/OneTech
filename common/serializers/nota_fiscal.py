from rest_framework import serializers
from nota_fiscal.models import NotaFiscal, TransporteNotaFiscal, DuplicataNotaFiscal
from nota_fiscal.models import EntradaProduto


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
    produtos = serializers.SerializerMethodField()
    transporte = serializers.SerializerMethodField()
    duplicatas = serializers.SerializerMethodField()

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
            'produtos',
            'transporte',
            'duplicatas',
        ]

    def get_usuario(self, obj):
        if obj.created_by:
            return obj.created_by.username
        return ''

    def get_produtos(self, obj):
        produtos = EntradaProduto.objects.filter(numero_nota=obj.numero)
        return [
            {
                'codigo': p.produto.codigo,
                'nome': p.produto.nome,
                'quantidade': str(p.quantidade),
                'valor_unitario': str(p.preco_unitario),
                'valor_total': str(p.preco_total),
                'cfop': p.produto.cfop,
                'unidade': p.produto.unidade_comercial,
                'icms': str(p.icms_aliquota or 0),
                'ipi': str(p.ipi_aliquota or 0),
                'desconto': '0.00'  # adicione lógica real se houver
            }
            for p in produtos
        ]

    def get_transporte(self, obj):
        try:
            t = obj.transportenotafiscal
            return {
                'modalidade_frete': t.modalidade_frete,
                'transportadora_nome': t.transportadora_nome,
                'transportadora_cnpj': t.transportadora_cnpj,
                'placa_veiculo': t.placa_veiculo,
                'uf_veiculo': t.uf_veiculo,
                'rntc': t.rntc,
                'quantidade_volumes': t.quantidade_volumes,
                'especie_volumes': t.especie_volumes,
                'peso_liquido': str(t.peso_liquido),
                'peso_bruto': str(t.peso_bruto),
            }
        except TransporteNotaFiscal.DoesNotExist:
            return None

    def get_duplicatas(self, obj):
        duplicatas = DuplicataNotaFiscal.objects.filter(nota_fiscal=obj)
        return [
            {
                'numero': d.numero,
                'valor': str(d.valor),
                'vencimento': d.vencimento.strftime('%Y-%m-%d') if d.vencimento else ''
            }
            for d in duplicatas
        ]
