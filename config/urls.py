from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from accounts.views import login_view
from django.views.generic.base import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage

def home_redirect_view(request):
    if request.user.is_authenticated:
        return redirect('painel:home')
    else:
        return redirect('accounts:login')

urlpatterns = [
    # 🔹 Administração do Django
    path('admin/', admin.site.urls),

    # 🔹 Administração Customizada (Tenants, etc.)
    path('gerenciamento/', include('control.urls', namespace='control')),

    # 🔹 Módulo de autenticação e gestão de usuários
    path('painel/', include('painel.urls', namespace='painel')), # Adiciona o namespace painel explicitamente
    path('accounts/', include('accounts.urls', namespace='accounts')),

    # Produção (Tilápias) - Movido para cima para ser avaliado antes do redirecionamento genérico
    path('producao/', include('producao.urls', namespace='producao')),

    # 🔹 Painel principal (protegido por login) - Agora abaixo das URLs específicas
    path('', home_redirect_view, name='home_redirect'),

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

    # Comercial
    path('comercial/', include('comercial.urls', namespace='comercial')),

    # Integração NFe (Webhooks)
    path('integracao-nfe/', include('integracao_nfe.urls', namespace='integracao_nfe')),

    #  Favicon sempre servido da pasta static/icons/
    path(
        "favicon.ico",
        RedirectView.as_view(
            url=staticfiles_storage.url("icons/favicon.ico"),
            permanent=False
        ),
        name="favicon"
    ),
]

from django.conf import settings
from django.conf.urls.static import static

# serving media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)