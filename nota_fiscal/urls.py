# nota_fiscal/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from common.api.nota_fiscal import NotaFiscalViewSet

router = DefaultRouter()
router.register(r'notas-entradas', NotaFiscalViewSet, basename='nota-fiscal')

app_name = "nota_fiscal"

urlpatterns = [
    # --- API REST (se houver) ---
    path("api/v1/", include(router.urls)),

    # --- PÁGINAS RENDERIZADAS ---
    path("importar/", views.importar_xml_view, name="importar_xml"),
    path("entradas/", views.entradas_nota_view, name="entradas_nota"),
    path("lancar-manual/", views.lancar_nota_manual_view, name="lancar_nota_manual"),
    path("emitir/", views.emitir_nfe_list_view, name="emitir_nfe_list"),
    path("editar/<int:pk>/", views.editar_nota_view, name="editar_nota"),

    # --- API ENDPOINTS PARA O FRONTEND ---
    path("api/importar-xml-nfe/", views.importar_xml_nfe_view, name="api_importar_xml_nfe"),
    path("api/processar-importacao-xml/", views.processar_importacao_xml_view, name="api_processar_importacao_xml"),
    path("api/excluir-multiplo/", views.excluir_notas_multiplo_view, name="excluir_nota_multiplo"),
    path("api/buscar-produtos/", views.buscar_produtos_para_nota_view, name="buscar_produtos_para_nota"),
]
