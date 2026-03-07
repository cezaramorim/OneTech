# common/serializers/produto.py

from rest_framework import serializers
from produto.models import Produto, CategoriaProduto, UnidadeMedida, NCM, DetalhesFiscaisProduto
from empresas.models import Empresa


# Serializer da categoria do produto (nome e descricao)
class CategoriaProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaProduto
        fields = ['id', 'nome', 'descricao']


# Serializer da unidade de medida (sigla e descricao)
class UnidadeMedidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadeMedida
        fields = ['id', 'sigla', 'descricao']


# Serializer do NCM (codigo e descricao)
class NCMSerializer(serializers.ModelSerializer):
    class Meta:
        model = NCM
        fields = ['codigo', 'descricao']


# ðŸ”¹ Serializer do fornecedor (Empresa) com campos relevantes apenas
class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = [
            'id',
            'tipo_empresa',
            'razao_social',
            'nome_fantasia',
            'cnpj',
            'cpf',
            'email',
            'telefone',
            'status_empresa'
        ]
        # Apenas dados uteis para exibicao na API de produtos


# ðŸ”¹ Serializer para DetalhesFiscaisProduto
class DetalhesFiscaisProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalhesFiscaisProduto
        exclude = ['id', 'produto'] # Exclui campos que nao sao relevantes na representacao aninhada


# âœ… Serializer principal do Produto com relacionamentos aninhados
class ProdutoSerializer(serializers.ModelSerializer):
    categoria = CategoriaProdutoSerializer(read_only=True)
    unidade_medida = UnidadeMedidaSerializer(read_only=True)
    ncm = NCMSerializer(read_only=True)
    fornecedor = EmpresaSerializer(read_only=True)
    detalhes_fiscais = DetalhesFiscaisProdutoSerializer(read_only=True) # Aninha o serializer de detalhes fiscais

    class Meta:
        model = Produto
        fields = '__all__'
        # Inclui todos os campos do produto e substitui FK por dados legiveis
