# common/serializers/produto.py

from rest_framework import serializers
from produto.models import Produto, CategoriaProduto, UnidadeMedida, NCM, DetalhesFiscaisProduto
from empresas.models import EmpresaAvancada


# 🔹 Serializer da categoria do produto (nome e descrição)
class CategoriaProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaProduto
        fields = ['id', 'nome', 'descricao']


# 🔹 Serializer da unidade de medida (sigla e descrição)
class UnidadeMedidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadeMedida
        fields = ['id', 'sigla', 'descricao']


# 🔹 Serializer do NCM (código e descrição)
class NCMSerializer(serializers.ModelSerializer):
    class Meta:
        model = NCM
        fields = ['codigo', 'descricao']


# 🔹 Serializer do fornecedor (EmpresaAvancada) com campos relevantes apenas
class EmpresaAvancadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpresaAvancada
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
        # 🔒 Apenas dados úteis para exibição na API de produtos


# 🔹 Serializer para DetalhesFiscaisProduto
class DetalhesFiscaisProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalhesFiscaisProduto
        exclude = ['id', 'produto'] # Exclui campos que não são relevantes na representação aninhada


# ✅ Serializer principal do Produto com relacionamentos aninhados
class ProdutoSerializer(serializers.ModelSerializer):
    categoria = CategoriaProdutoSerializer(read_only=True)
    unidade_medida = UnidadeMedidaSerializer(read_only=True)
    ncm = NCMSerializer(read_only=True)
    fornecedor = EmpresaAvancadaSerializer(read_only=True)
    detalhes_fiscais = DetalhesFiscaisProdutoSerializer(read_only=True) # Aninha o serializer de detalhes fiscais

    class Meta:
        model = Produto
        fields = '__all__'
        # 🔁 Inclui todos os campos do produto e substitui FK por dados legíveis
