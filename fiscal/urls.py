from django.urls import path
from . import views

app_name = 'fiscal'

urlpatterns = [
    # URLs para CFOP
    path('cfops/', views.cfop_list, name='cfop_list'),
    path('cfops/cadastrar/', views.cfop_create, name='cfop_create'),
    path('cfops/editar/<int:pk>/', views.cfop_update, name='cfop_update'),

    # URLs para Natureza de Operação
    path('naturezas-operacao/', views.natureza_operacao_list, name='natureza_operacao_list'),
    path('naturezas-operacao/cadastrar/', views.natureza_operacao_create, name='natureza_operacao_create'),
    path('naturezas-operacao/editar/<int:pk>/', views.natureza_operacao_update, name='natureza_operacao_update'),

    # URLs para Importação de Excel
    path('importar-dados/', views.import_fiscal_data_view, name='import_fiscal_data'),
    path('download-template/', views.download_fiscal_template_view, name='download_fiscal_template'),
    path('delete-items/', views.delete_fiscal_items, name='delete_fiscal_items'),
]