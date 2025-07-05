from django.urls import path
from . import views

app_name = 'integracao_nfe'

urlpatterns = [
    path('webhook/sefaz/', views.sefaz_webhook, name='sefaz_webhook'),
]