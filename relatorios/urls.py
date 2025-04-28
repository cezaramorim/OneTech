# relatorios/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from relatorios.api import NotaFiscalViewSet
from relatorios.views import notas_entradas_view, editar_entrada_view

app_name = 'relatorios'

# === Configura DRF router para /api/v1/notas-entradas/ ===
router = DefaultRouter()
router.register(r'notas-entradas', NotaFiscalViewSet, basename='notas-entradas')

urlpatterns = [
    # página completa e partial
    path('', notas_entradas_view, name='notas_entradas'),
    path('entradas/<int:pk>/editar/', editar_entrada_view, name='editar_entrada'),

    # endpoints REST em /api/v1/...
    path('api/v1/', include(router.urls)),
]
