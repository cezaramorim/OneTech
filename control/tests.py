from django.test import TestCase
from unittest.mock import Mock

from control.db_router import TenantRouter
from control.utils import get_current_tenant, set_current_tenant, use_tenant
from control.models import Tenant
from accounts.models import User
from django.contrib.auth.models import Group

class TenantContextTests(TestCase):
    """
    Testa as funções de gerenciamento de contexto do tenant (get/set/use).
    Estes testes são rápidos e não tocam no banco de dados.
    """
    def test_get_and_set_current_tenant(self):
        """
        Testa se o tenant pode ser definido e recuperado corretamente na thread atual.
        """
        self.assertIsNone(get_current_tenant(), "O tenant deveria ser None inicialmente.")
        
        mock_tenant = Mock()
        mock_tenant.name = "Tenant Mock"
        
        set_current_tenant(mock_tenant)
        self.assertEqual(get_current_tenant(), mock_tenant)
        
        set_current_tenant(None)
        self.assertIsNone(get_current_tenant(), "O tenant deveria ser None após ser limpo.")

    def test_use_tenant_context_manager(self):
        """
        Testa se o context manager 'use_tenant' define e restaura o contexto corretamente.
        """
        # Mocks de tenant com os atributos mínimos necessários para o 'use_tenant'
        mock_tenant_1 = Mock(db_name='db_mock_1', name="Tenant 1")
        mock_tenant_2 = Mock(db_name='db_mock_2', name="Tenant 2")

        self.assertIsNone(get_current_tenant(), "O tenant deveria ser None antes de entrar no contexto.")

        with use_tenant(mock_tenant_1):
            self.assertEqual(get_current_tenant(), mock_tenant_1, "Deveria estar no contexto do Tenant 1.")
            
            # Testa o aninhamento de contextos
            with use_tenant(mock_tenant_2):
                self.assertEqual(get_current_tenant(), mock_tenant_2, "Deveria estar no contexto aninhado do Tenant 2.")
            
            self.assertEqual(get_current_tenant(), mock_tenant_1, "Deveria ter restaurado para o contexto do Tenant 1.")

        self.assertIsNone(get_current_tenant(), "O tenant deveria ser None após sair de todos os contextos.")


class TenantRouterTests(TestCase):
    """
    Testa a lógica de decisão do TenantRouter em memória, sem acessar o banco de dados.
    """
    def setUp(self):
        """Configura o router e um tenant mock para os testes."""
        self.router = TenantRouter()
        self.mock_tenant = Mock()
        self.mock_tenant.db_name = "db_do_tenant_mock"

    def tearDown(self):
        """Garante que o contexto seja limpo após cada teste."""
        set_current_tenant(None)

    def test_control_app_models_route_to_default(self):
        """
        Testa se modelos de apps de controle (Tenant, Group) são sempre roteados para 'default'.
        """
        # Testa sem nenhum tenant no contexto
        self.assertEqual(self.router.db_for_read(Tenant), 'default')
        self.assertEqual(self.router.db_for_write(Tenant), 'default')
        self.assertEqual(self.router.db_for_read(Group), 'default')
        self.assertEqual(self.router.db_for_write(Group), 'default')

        # Testa com um tenant ativo no contexto - o resultado deve ser o mesmo
        with use_tenant(self.mock_tenant):
            self.assertEqual(self.router.db_for_read(Tenant), 'default')
            self.assertEqual(self.router.db_for_write(Tenant), 'default')
            self.assertEqual(self.router.db_for_read(Group), 'default')
            self.assertEqual(self.router.db_for_write(Group), 'default')

    def test_tenant_app_models_route_to_tenant_db(self):
        """
        Testa se modelos de apps de tenant (User) são roteados para o DB do tenant quando o contexto está ativo.
        """
        with use_tenant(self.mock_tenant):
            self.assertEqual(self.router.db_for_read(User), self.mock_tenant.db_name)
            self.assertEqual(self.router.db_for_write(User), self.mock_tenant.db_name)

    def test_tenant_app_models_route_to_default_when_no_tenant(self):
        """
        Testa se modelos de apps de tenant são roteados para 'default' se nenhum tenant estiver ativo.
        """
        set_current_tenant(None)
        self.assertEqual(self.router.db_for_read(User), 'default')
        self.assertEqual(self.router.db_for_write(User), 'default')

    def test_allow_migrate_logic(self):
        """
        Testa a lógica de permissão de migração do roteador.
        """
        # Apps de controle só podem migrar no 'default'
        self.assertTrue(self.router.allow_migrate('default', 'control'))
        self.assertTrue(self.router.allow_migrate('default', 'auth'))
        self.assertFalse(self.router.allow_migrate('db_de_tenant', 'control'))
        self.assertFalse(self.router.allow_migrate('db_de_tenant', 'auth'))

        # Apps de tenant só podem migrar em bancos que NÃO são 'default'
        self.assertFalse(self.router.allow_migrate('default', 'accounts'))
        self.assertFalse(self.router.allow_migrate('default', 'empresas'))
        self.assertTrue(self.router.allow_migrate('db_de_tenant', 'accounts'))
        self.assertTrue(self.router.allow_migrate('db_de_tenant', 'empresas'))
