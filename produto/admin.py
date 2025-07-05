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
    list_display = ('codigo', 'nome', 'categoria', 'unidade_medida_interna', 'preco_venda', 'estoque_atual', 'ativo')
    list_filter = ('categoria', 'unidade_medida_interna', 'ativo')
    search_fields = ('codigo', 'nome', 'descricao', 'ncm')
    readonly_fields = ('preco_medio', 'estoque_atual')
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo', 'nome', 'descricao', 'categoria', 'ncm', 'cfop')
        }),
        ('Comercial', {
            'fields': ('unidade_medida_interna', 'preco_custo', 'preco_venda', 'preco_medio')
        }),
        ('Estoque', {
            'fields': ('estoque_total', 'quantidade_saidas', 'estoque_atual', 'controla_estoque')
        }),
        ('Status e Outros', {
            'fields': ('ativo', 'data_cadastro', 'observacoes')
        }),
    )


# Estrutura do menu lateral (painel) deve incluir:
# Produtos
# ├── Listar Produtos
# ├── Categorias de Produto
# └── Unidades de Medida

# No HTML do menu lateral (ex: base.html ou sidebar.html):
# <li class="nav-item">
#   <a class="nav-link" data-url="/produtos/" href="#">
#     <i class="bi bi-box-seam"></i> Produtos
#   </a>
#   <ul class="submenu">
#     <li><a href="#" data-url="/produtos/">Listar Produtos</a></li>
#     <li><a href="#" data-url="/produtos/categorias/">Categorias de Produto</a></li>
#     <li><a href="#" data-url="/produtos/unidades/">Unidades de Medida</a></li>
#   </ul>
# </li>
