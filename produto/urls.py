from django.urls import path
from . import views

app_name = "produto"

urlpatterns = [
    # Produtos
    path("", views.lista_produtos_view, name="lista_produtos"),
    path("novo/", views.cadastrar_produto_view, name="cadastrar_produto"),

    # Categorias
    path("categorias/", views.lista_categorias_view, name="lista_categorias"),
    path("categorias/nova/", views.cadastrar_categoria_view, name="cadastrar_categoria"),

    # Unidades
    path("unidades/", views.lista_unidades_view, name="lista_unidades"),
    path("unidades/nova/", views.cadastrar_unidade_view, name="cadastrar_unidade"),

    # NCM
    path("ncm/", views.manutencao_ncm_view, name="manutencao_ncm"),
    path("ncm/importar/", views.importar_ncm_manual_view, name="importar_ncm_manual"),
    path("ncm-autocomplete/", views.ncm_autocomplete_view, name="ncm_autocomplete"),
    path('buscar-ncm/', views.buscar_ncm_ajax, name='buscar_ncm_ajax'),
]

