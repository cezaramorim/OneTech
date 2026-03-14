# control/middleware.py
import logging
from django.shortcuts import redirect
from django.core.cache import cache
from django.http import JsonResponse
from .models import Tenant
from .utils import is_principal_context, set_current_tenant

logger = logging.getLogger(__name__)


def _tenant_quarantine_cache_key(tenant_slug):
    return f'security:tenant-quarantine:{tenant_slug}'


class TenantMiddleware:
    """
    Middleware novo-estilo para seleção de Tenant por host.
    Sua única responsabilidade é identificar o tenant pelo domínio
    e o definir no contexto da requisição usando um thread-local.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        logger.info(f"Carregando TenantMiddleware simplificado do módulo: {__name__}")

    def __call__(self, request):
        # Limpa o tenant da requisição anterior
        set_current_tenant(None)
        request.tenant = None

        host = request.get_host().split(":")[0].lower()

        try:
            tenant = Tenant.objects.using("default").filter(dominio=host, ativo=True).first()
            if tenant:
                set_current_tenant(tenant)
                request.tenant = tenant
        except Exception:
            # Se ocorrer um erro (ex: banco de dados 'default' indisponível),
            # loga o erro mas permite que a aplicação continue (pode ser uma página de erro do Django).
            logger.exception("Erro no TenantMiddleware ao resolver tenant para host '%s'", host)

        if not is_principal_context(request) and request.path.startswith('/admin/'):
            return redirect('/painel/?admin_restrito=1')

        if request.tenant:
            quarantine_data = cache.get(_tenant_quarantine_cache_key(request.tenant.slug))
            tenant_quarentena_ativa = bool(quarantine_data)
            if tenant_quarentena_ativa and request.method not in {'GET', 'HEAD', 'OPTIONS'}:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse(
                        {
                            'success': False,
                            'code': 'tenant_quarantine_active',
                            'message': 'Tenant em quarentena (modo leitura). Operacao bloqueada temporariamente.',
                        },
                        status=423,
                    )
                return redirect('/painel/?tenant_quarentena=1')

        response = self.get_response(request)
        return response
