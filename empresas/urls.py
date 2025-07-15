from django.urls import path
from . import views
from .views import empresa_avancada_form_view
from rest_framework.routers import DefaultRouter
from common.api.empresa import FornecedorViewSet

app_name = 'empresas'

# 🔁 API de Fornecedores (EmpresaAvancada) via ViewSet
router = DefaultRouter()
router.register(r'api/v1/fornecedores', FornecedorViewSet, basename='fornecedores')

# 🔹 URLs padrão da área de empresas
urlpatterns = [
    # Empresas
    #path('cadastrar/', views.cadastrar_empresa, name='cadastrar_empresa'),    
    #path('lista/', views.lista_empresas, name='lista_empresas'),
    #path('editar/<int:empresa_id>/', views.editar_empresa, name='editar_empresa'),
    #path('excluir-multiplo/', views.excluir_empresa_multiplo, name='excluir_empresa_multiplo'),

    # Categorias
    path('categorias/', views.lista_categorias_view, name='lista_categorias'),
    path('nova-avancada/categoria/', views.categoria_form_view, name='cadastrar_categoria_avancada_new'),
    path('categorias/<int:pk>/editar/', views.categoria_form_view, name='editar_categoria'),
    path('categorias/excluir-multiplos/', views.excluir_categorias_view, name='excluir_categorias_multiplos'),

    # Empresas Avançadas
    path('nova-avancada/', views.empresa_avancada_form_view, name='cadastrar_empresa_avancada'),
    path('avancadas/', views.lista_empresas_avancadas_view, name='lista_empresas_avancadas'),
    path('avancadas/<int:pk>/atualizar-status/', views.atualizar_status_empresa_avancada, name='atualizar_status_empresa_avancada'),
    path('avancadas/<int:pk>/editar/', views.empresa_avancada_form_view, name='editar_empresa_avancada'),

]

# 🔁 Adiciona as rotas da API REST ao final
urlpatterns += router.urls
