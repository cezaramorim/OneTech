from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from accounts.views import login_view

def home_redirect_view(request):
    if request.user.is_authenticated:
        return redirect('painel:home')
    else:
        return redirect('accounts:login')

urlpatterns = [
    # 🔹 Administração do Django
    path('admin/', admin.site.urls),

    # 🔹 Painel principal (protegido por login)
    path('', home_redirect_view, name='home_redirect'),

    # 🔹 Módulo de autenticação e gestão de usuários
    path('painel/', include('painel.urls', namespace='painel')), # Adiciona o namespace painel explicitamente
    path('accounts/', include('accounts.urls', namespace='accounts')),

    # 🔹 Módulo de empresas e categorias
    path('empresas/', include('empresas.urls', namespace='empresas')),
    path('login/', lambda request: redirect('accounts:login')),
    
    # Produtos
    path("produtos/", include("produto.urls")),
    
    # Nota Fiscal
    path('nota-fiscal/', include('nota_fiscal.urls', namespace='nota_fiscal')),
   
   # expõe seus ViewSets do common em /api/v1/
    path('api/v1/', include('common.api.urls')),
 
    # <-- monta todas as rotas de API do nota_fiscal
   # path('api/', include('nota_fiscal.api.urls')),
    
    # Relatórios
    path('relatorios/', include('relatorios.urls', namespace='relatorios')),

    # Fiscal
    path('fiscal/', include('fiscal.urls', namespace='fiscal')),

    # Integração NFe (Webhooks)
    path('integracao-nfe/', include('integracao_nfe.urls', namespace='integracao_nfe')),
]
