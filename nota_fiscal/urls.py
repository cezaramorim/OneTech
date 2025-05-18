# nota_fiscal/urls.py
# nota_fiscal/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    importar_xml_view,
    importar_xml_nfe_view,
    salvar_importacao_view,
    editar_entrada_view,
    entradas_nota_view,
    excluir_entrada_view,
)

from common.api.nota_fiscal import NotaFiscalViewSet

router = DefaultRouter()
router.register(r'notas-entradas', NotaFiscalViewSet, basename='nota-fiscal')

app_name = "nota_fiscal"

urlpatterns = [
    path("api/v1/", include(router.urls)),

    path("importar/", importar_xml_view, name="importar_xml"),
    path("importar/processar/", importar_xml_nfe_view, name="importar_xml_nfe"),
    path("importar/salvar/", salvar_importacao_view, name="salvar_importacao"),
    path("entradas/", entradas_nota_view, name="entradas_nota"),
    path("editar/<int:pk>/", editar_entrada_view, name="editar_entrada"),
    path("excluir/<int:pk>/", excluir_entrada_view, name="excluir_entrada"),
]
