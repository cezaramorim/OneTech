# control/middleware.py
import logging
from .models import Tenant
from .utils import set_current_tenant

logger = logging.getLogger(__name__)

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

        response = self.get_response(request)
        return response
