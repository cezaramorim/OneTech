from django.urls import path
from . import views
from .views import cadastrar_empresa_avancada
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
    path('nova-avancada/categoria/', views.cadastrar_categoria_avancada, name='cadastrar_categoria_avancada'),

    # Empresas Avançadas
    path('nova-avancada/', cadastrar_empresa_avancada, name='cadastrar_empresa_avancada'),
    path('avancadas/', views.lista_empresas_avancadas_view, name='lista_empresas_avancadas'),
    path('avancadas/<int:pk>/atualizar-status/', views.atualizar_status_empresa_avancada, name='atualizar_status_empresa_avancada'),
    path('avancadas/<int:pk>/editar/', views.editar_empresa_avancada_view, name='editar_empresa_avancada'),

]

# 🔁 Adiciona as rotas da API REST ao final
urlpatterns += router.urls
