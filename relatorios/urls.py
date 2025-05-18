# relatorios/urls.py

from django.urls import path
from relatorios.views import api_nota_detalhada, relatorio_nota_fiscal_view

app_name = 'relatorios'

urlpatterns = [
    path("api/v1/notas-entradas/<int:pk>/", api_nota_detalhada, name="api_nota_detalhada"),
    path("nota-fiscal/", relatorio_nota_fiscal_view, name="relatorio_nota_fiscal"),
]
