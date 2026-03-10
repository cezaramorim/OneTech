from django.urls import path

from . import views

app_name = 'fiscal_regras'

urlpatterns = [
    path('', views.regra_icms_list, name='regra_icms_list'),
    path('cadastrar/', views.regra_icms_create, name='regra_icms_create'),
    path('editar/<int:pk>/', views.regra_icms_update, name='regra_icms_update'),
    path('excluir-selecionados/', views.delete_regras_icms, name='delete_regras_icms'),
    path('importar/', views.importar_regras_view, name='importar_regras'),
    path('validar/', views.validar_regras_view, name='validar_regras'),
    path('exportar/', views.exportar_regras_view, name='exportar_regras'),
    path('api/resolver-icms/', views.resolver_aliquota_icms_api, name='resolver_aliquota_icms_api'),
]
