from django.urls import path
from . import views
from .views import cadastrar_empresa_avancado

app_name = 'empresas'

urlpatterns = [
    # 🔹 EMPRESAS
    path('cadastrar/', views.cadastrar_empresa, name='cadastrar_empresa'),  # Cadastro Simples
    path('nova-avancada/', cadastrar_empresa_avancado, name='cadastrar_empresa_avancado'),  # Cadastro Avançado
    path('lista/', views.lista_empresas, name='lista_empresas'),
    path('editar/<int:empresa_id>/', views.editar_empresa, name='editar_empresa'),
    path('excluir-multiplo/', views.excluir_empresa_multiplo, name='excluir_empresa_multiplo'),  # ✅ NOVO

    # 🔹 CATEGORIAS
    path('nova-avancada/categoria/', views.cadastrar_categoria_avancada, name='cadastrar_categoria_avancada'),
]
