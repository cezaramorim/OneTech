from django.urls import path
from . import views

app_name = 'empresas'

urlpatterns = [
    # 🔹 EMPRESAS
    path('cadastrar/', views.cadastrar_empresa, name='cadastrar_empresa'),
    path('lista/', views.lista_empresas, name='lista_empresas'),
    path('editar/<int:empresa_id>/', views.editar_empresa, name='editar_empresa'),
    path('excluir-multiplo/', views.excluir_empresa_multiplo, name='excluir_empresa_multiplo'),  # ✅ NOVO

    # 🔹 CATEGORIAS
    path('categoria/cadastrar/', views.cadastrar_categoria, name='cadastrar_categoria'),
]
