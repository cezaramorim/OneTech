# control/utils.py
import threading
from contextlib import contextmanager
from django.conf import settings
from django.db import connections

# Usando threading.local para garantir que o contexto do tenant seja thread-safe,
# especialmente em ambientes com múltiplas requisições simultâneas.
_tenant_local = threading.local()

def get_current_tenant():
    """
    Retorna o tenant ativo no contexto da thread atual.
    Retorna None se nenhum tenant estiver ativo.
    """
    return getattr(_tenant_local, "tenant", None)

def set_current_tenant(tenant):
    """
    Define o tenant ativo para o contexto da thread atual.
    Usado pelo TenantMiddleware e pelo context manager use_tenant.
    """
    _tenant_local.tenant = tenant

@contextmanager
def use_tenant(tenant):
    """
    Um context manager para executar um bloco de código no contexto de um tenant específico.
    Apenas define o tenant na thread atual; o DatabaseRouter cuidará da conexão.
    """
    previous_tenant = get_current_tenant()
    set_current_tenant(tenant)
    try:
        yield
    finally:
        set_current_tenant(previous_tenant)


def tenant_media_path(instance, filename):
    """
    Gera um path de upload dinâmico para arquivos de um tenant,
    garantindo o isolamento dos arquivos de mídia.
    Ex: tenants/cliente-a/app_label/model_name/arquivo.pdf
    """
    # A importação é feita aqui para evitar importação circular
    from .models import Tenant
    
    slug = 'shared' # Fallback
    if isinstance(instance, Tenant):
        # Se a instância é o próprio Tenant, usamos seu slug
        slug = instance.slug
    else:
        # Para outros modelos, tentamos obter o tenant do contexto da thread
        tenant = get_current_tenant()
        if tenant:
            slug = tenant.slug

    app_label = instance._meta.app_label
    model_name = instance._meta.model_name
    return f'tenants/{slug}/{app_label}/{model_name}/{filename}'
