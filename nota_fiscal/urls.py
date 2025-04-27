from django.urls import path
from . import views

app_name = 'nota_fiscal'

urlpatterns = [
    path('importar/', views.importar_xml_view, name='importar_xml'),            # Formulário de importação
    path('importar/upload/', views.importar_xml_nfe_view, name='importar_xml_upload'),  # Upload XML
    path('importar/salvar/', views.salvar_importacao_view, name='importar_xml_salvar'), # 🚨 SALVAR Importação
]
