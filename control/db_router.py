# control/db_router.py
import logging
from django.conf import settings
from django.db import connections
from .utils import get_current_tenant

logger = logging.getLogger(__name__)

# Apps que devem usar o banco de dados específico do tenant
TENANT_APPS = getattr(settings, "TENANT_APPS", ())

class TenantRouter:
    """
    Router para bancos multi-tenant que direciona queries para o banco correto.

    - Apps listadas em `TENANT_APPS` são direcionadas para o banco do tenant ativo.
    - As demais apps (consideradas 'globais' ou de 'controle') usam o banco 'default'.
    - A conexão do tenant é configurada dinamicamente em `connections.databases`
      usando um alias fixo ('tenant'), sem modificar `settings.DATABASES`.
    """
    tenant_alias = "tenant"
    control_apps = [app.split('.')[-1] for app in settings.INSTALLED_APPS if app not in TENANT_APPS]

    def _is_tenant_app(self, app_label: str) -> bool:
        return app_label in TENANT_APPS

    def _configure_tenant_db(self, tenant):
        """
        Configura a conexão do banco de dados do tenant em tempo de execução.
        Usa a configuração 'default' como base e a atualiza com os dados do tenant.
        """
        if tenant is None:
            return "default"

        # Se a conexão já estiver configurada e for para o mesmo banco, não faz nada.
        if self.tenant_alias in connections.databases and connections.databases[self.tenant_alias]['NAME'] == tenant.db_name:
            return self.tenant_alias

        base_cfg = settings.DATABASES["default"].copy()
        base_cfg.update({
            "NAME": tenant.db_name,
            "USER": tenant.db_user,
            "PASSWORD": tenant.db_password,
            "HOST": tenant.db_host,
            "PORT": tenant.db_port,
        })
        connections.databases[self.tenant_alias] = base_cfg
        return self.tenant_alias

    def db_for_read(self, model, **hints):
        if model._meta.app_label in TENANT_APPS:
            tenant = get_current_tenant()
            if tenant:
                return self._configure_tenant_db(tenant)
        return "default"

    def db_for_write(self, model, **hints):
        if model._meta.app_label in TENANT_APPS:
            tenant = get_current_tenant()
            if tenant:
                return self._configure_tenant_db(tenant)
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        obj1_is_tenant = obj1._meta.app_label in TENANT_APPS
        obj2_is_tenant = obj2._meta.app_label in TENANT_APPS
        
        # Permite relações se ambos os objetos pertencem ao mesmo "escopo" (ambos tenant ou ambos não-tenant)
        if obj1_is_tenant == obj2_is_tenant:
            return True
        return False

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        is_tenant_app = app_label in TENANT_APPS

        if db == 'default':
            # No banco 'default', só permite migrar apps que NÃO são de tenant.
            return not is_tenant_app
        else:
            # Em qualquer outro banco (que será um banco de tenant),
            # só permite migrar apps que SÃO de tenant.
            return is_tenant_app