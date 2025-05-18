from django.urls import path, include
from . import views
from nota_fiscal.views import editar_entrada_view

# 🔹 View API simples com @api_view
#from common.api.produto import listar_produtos_json

# 🔹 ViewSet para API REST completa
from rest_framework.routers import DefaultRouter
from common.api.produto import ProdutoViewSet

app_name = "produto"

# 🔹 Router separado da lista
router = DefaultRouter()
router.register(r'api/v1/produtos', ProdutoViewSet, basename='produto')

urlpatterns = [
    # Produtos
    path("", views.lista_produtos_view, name="lista_produtos"),
    path("novo/", views.cadastrar_produto_view, name="cadastrar_produto"),

    # Categorias
    path("categorias/", views.lista_categorias_view, name="lista_categorias"),
    path("categorias/nova/", views.cadastrar_categoria_view, name="cadastrar_categoria"),
    path("categorias/editar/<int:pk>/", views.editar_categoria_view, name="editar_categoria"),
    path("categorias/excluir-multiplas/", views.excluir_categorias_view, name="excluir_categorias"),

    # Unidades
    path("unidades/", views.lista_unidades_view, name="lista_unidades"),
    path("unidades/nova/", views.cadastrar_unidade_view, name="cadastrar_unidade"),

    # NCM
    path("ncm/", views.manutencao_ncm_view, name="manutencao_ncm"),
    path("ncm/importar/", views.importar_ncm_manual_view, name="importar_ncm_manual"),
    path("buscar-ncm/", views.buscar_ncm_ajax, name="buscar_ncm_ajax"),
    path("ncm-autocomplete-produto/", views.buscar_ncm_descricao_ajax, name="ncm_autocomplete"),

    # XML NFe
    path("importar-xml-nfe/", views.importar_xml_nfe_view, name="importar_xml_nfe"),

    # Produtos - Edição e exclusão
    path("excluir-multiplos/", views.excluir_produtos_view, name="excluir_produtos"),
    path("editar/<int:pk>/", views.editar_produto_view, name="editar_produto"),

    # API JSON simples
    #path("api/json/", listar_produtos_json, name="listar_produtos_json"),
]

# ✅ Inclui as rotas da API REST (ViewSet)
urlpatterns += router.urls


