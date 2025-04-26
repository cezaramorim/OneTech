from django.urls import path
from . import views

app_name = 'nota_fiscal'

urlpatterns = [
    path('importar/', views.importar_xml_view, name='importar_xml'),           # Carrega a página do formulário
    path('importar/upload/', views.importar_xml_nfe_view, name='importar_xml_upload'),  # Recebe o POST do upload
]
