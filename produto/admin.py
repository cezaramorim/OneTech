from django.contrib import admin
from .models import Produto, CategoriaProduto, UnidadeMedida


@admin.register(CategoriaProduto)
class CategoriaProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)


@admin.register(UnidadeMedida)
class UnidadeMedidaAdmin(admin.ModelAdmin):
    list_display = ('sigla', 'descricao')
    search_fields = ('sigla', 'descricao')


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('codigo_interno', 'codigo_fornecedor', 'nome', 'categoria', 'unidade_medida_interna', 'preco_custo', 'estoque_atual', 'ativo')
    list_filter = ('categoria', 'unidade_medida_interna', 'ativo')
    search_fields = ('codigo_interno', 'codigo_fornecedor', 'nome')
    readonly_fields = ('codigo_interno', 'preco_medio', 'estoque_atual')
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo_fornecedor', 'nome', 'categoria')
        }),
        ('Comercial', {
            'fields': ('unidade_medida_interna', 'fator_conversao', 'preco_custo', 'preco_venda', 'preco_medio')
        }),
        ('Estoque', {
            'fields': ('estoque_total', 'quantidade_saidas', 'estoque_atual', 'controla_estoque')
        }),
        ('Status e Outros', {
            'fields': ('ativo', 'data_cadastro', 'observacoes')
        }),
    )