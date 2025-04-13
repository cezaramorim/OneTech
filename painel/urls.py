from django.urls import path
from .views import painel_onetech

app_name = 'painel'  # Permite o uso de {% url 'painel:home' %} nos templates

urlpatterns = [
    # Rota principal do sistema (renderiza base.html)
    path('', painel_onetech, name='home'),
]
