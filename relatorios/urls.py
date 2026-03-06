# relatorios/urls.py

from django.urls import path
from relatorios.views import (
    api_nota_detalhada,
    relatorio_nota_fiscal_view,
    impressao_relatorios_view,
    impressao_relatorios_preview_view,
    impressao_relatorios_download_csv_view,
)

app_name = 'relatorios'

urlpatterns = [
    path("api/v1/notas-entradas/<int:pk>/", api_nota_detalhada, name="api_nota_detalhada"),
    path("nota-fiscal/", relatorio_nota_fiscal_view, name="relatorio_nota_fiscal"),
    path("impressao/", impressao_relatorios_view, name="impressao_relatorios"),
    path("impressao/preview/", impressao_relatorios_preview_view, name="impressao_relatorios_preview"),
    path("impressao/download-csv/", impressao_relatorios_download_csv_view, name="impressao_relatorios_download_csv"),
]
