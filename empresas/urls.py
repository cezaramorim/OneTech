from django.urls import path
from rest_framework.routers import DefaultRouter

from common.api.empresa import FornecedorViewSet

from . import views

app_name = 'empresas'


# API de fornecedores baseada no cadastro oficial de empresas.
router = DefaultRouter()
router.register(r'api/v1/fornecedores', FornecedorViewSet, basename='fornecedores')


urlpatterns = [
    # Categorias
    path('categorias/', views.lista_categorias_view, name='lista_categorias'),
    path('nova-avancada/categoria/', views.categoria_form_view, name='cadastrar_categoria_avancada_new'),
    path('categorias/<int:pk>/editar/', views.categoria_form_view, name='editar_categoria'),
    path('categorias/excluir-multiplos/', views.excluir_categorias_view, name='excluir_categorias_multiplos'),

    # Fluxo canonico de empresas
    path('', views.lista_empresas_view, name='lista_empresas'),
    path('nova/', views.empresa_form_view, name='cadastrar_empresa'),
    path('<int:pk>/editar/', views.empresa_form_view, name='editar_empresa'),
    path('<int:pk>/atualizar-status/', views.atualizar_status_empresa, name='atualizar_status_empresa'),
    path('excluir-multiplos/', views.excluir_empresas_view, name='excluir_empresas_multiplos'),

]

urlpatterns += router.urls
