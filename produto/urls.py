# produto/urls.py

from django.urls import path, include
from . import views # Importa as views do próprio app produto
# Importa as views do app nota_fiscal, mas 'editar_entrada_view' foi removida na refatoração
# Você pode ter outras views de nota_fiscal que ainda precise importar aqui,
# mas 'editar_entrada_view' especificamente deve ser removida.
# Se você tiver outras views de nota_fiscal que usa AQUI no produto/urls.py,
# ajuste a importação para elas. Caso contrário, remova esta linha se não for usar mais nenhuma.
# from nota_fiscal.views import editar_entrada_view # <--- LINHA REMOVIDA/COMENTADA!

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
    path("<int:pk>/editar/", views.editar_produto_view, name="editar_produto"),
    path("excluir-multiplos/", views.excluir_produtos_multiplos_view, name="excluir_produto_multiplo"),

    # Categorias
    path("categorias/", views.lista_categorias_view, name="lista_categorias"),
    path("categorias/nova/", views.cadastrar_categoria_view, name="cadastrar_categoria"),
    path("categorias/<int:pk>/editar/", views.editar_categoria_view, name="editar_categoria"),
    path("categorias/excluir-multiplas/", views.excluir_categorias_view, name="excluir_categorias"),
    path('api/categorias/', views.categoria_list_api, name='categoria-list-api'),

    # Unidades
    path("unidades/", views.lista_unidades_view, name="lista_unidades"),
    path("unidades-medida/nova/", views.cadastrar_unidade_view, name="cadastrar_unidade"),
    path("unidades-medida/<int:pk>/editar/", views.editar_unidade_view, name="editar_unidade"), # Nova URL
    path("unidades-medida/excluir-multiplos/", views.excluir_unidades_view, name="excluir_unidades"), # Nova URL

    # NCM
    path("ncm/", views.manutencao_ncm_view, name="manutencao_ncm"),
    path("ncm/importar/", views.importar_ncm_manual_view, name="importar_ncm_manual"),
    path("buscar-ncm/", views.buscar_ncm_ajax, name="buscar_ncm_ajax"),
    path("ncm-autocomplete-produto/", views.buscar_ncm_ajax, name="ncm_autocomplete"),
    path("api/racoes/", views.api_racoes_list, name="api_racoes_list"),

    
]

# ✅ Inclui as rotas da API REST (ViewSet)
urlpatterns += router.urls
