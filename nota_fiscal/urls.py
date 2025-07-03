# nota_fiscal/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import importar_xml_view
from .views import importar_xml_nfe_view
from .views import processar_importacao_xml_view
from .views import entradas_nota_view
from .views import lancar_nota_manual_view
from .views import editar_nota_view # Importa a nova view de edição

from common.api.nota_fiscal import NotaFiscalViewSet

router = DefaultRouter()
router.register(r'notas-entradas', NotaFiscalViewSet, basename='nota-fiscal')

app_name = "nota_fiscal"

urlpatterns = [
    # --- API REST (se houver) ---
    path("api/v1/", include(router.urls)),

    # --- PÁGINAS RENDERIZADAS ---
    path("importar/", importar_xml_view, name="importar_xml"),
    path("entradas/", entradas_nota_view, name="entradas_nota"),
    path("lancar-manual/", lancar_nota_manual_view, name="lancar_nota_manual"),
    
    # Nova URL para editar a nota fiscal
    path("editar/<int:pk>/", editar_nota_view, name="editar_nota"),

    # --- API ENDPOINTS PARA O FRONTEND ---
    path("api/importar-xml-nfe/", importar_xml_nfe_view, name="api_importar_xml_nfe"),
    path("api/processar-importacao-xml/", processar_importacao_xml_view, name="api_processar_importacao_xml"),
]