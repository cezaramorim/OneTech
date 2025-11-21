# control/context_processors.py
from .utils import get_current_tenant

def tenant_branding(request):
    """
    Injeta o objeto do tenant (cliente) atual no contexto de todos os templates.

    Isso permite que os templates acessem informações como {{ empresa_atual.nome }}
    ou {{ empresa_atual.logo.url }} para customizar a interface.
    """
    return {
        'empresa_atual': get_current_tenant()
    }
