from django.urls import path
from . import views

app_name = 'integracao_nfe'

urlpatterns = [
    # URL para o sistema de terceiros notificar sobre o status da NF-e
    path('webhook/sefaz/', views.sefaz_webhook, name='webhook_sefaz'),
    
    # URL interna para iniciar o processo de emissão de uma NF-e
    path('emitir/', views.emitir_nota_fiscal_view, name='emitir_nfe'),
]
