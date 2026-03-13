from unittest import TestCase
from unittest.mock import Mock

from control.db_router import TenantRouter
from control.utils import get_current_tenant, set_current_tenant, use_tenant
from control.models import Tenant
from accounts.models import User
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.test import TestCase as DjangoTestCase
from django.urls import reverse


class TenantContextTests(TestCase):
    """
    Testa as funcoes de gerenciamento de contexto do tenant (get/set/use).
    Estes testes sao rapidos e nao tocam no banco de dados.
    """

    def test_get_and_set_current_tenant(self):
        self.assertIsNone(get_current_tenant(), "O tenant deveria ser None inicialmente.")

        mock_tenant = Mock()
        mock_tenant.name = "Tenant Mock"

        set_current_tenant(mock_tenant)
        self.assertEqual(get_current_tenant(), mock_tenant)

        set_current_tenant(None)
        self.assertIsNone(get_current_tenant(), "O tenant deveria ser None apos ser limpo.")

    def test_use_tenant_context_manager(self):
        mock_tenant_1 = Mock(db_name='db_mock_1', name="Tenant 1")
        mock_tenant_2 = Mock(db_name='db_mock_2', name="Tenant 2")

        self.assertIsNone(get_current_tenant(), "O tenant deveria ser None antes de entrar no contexto.")

        with use_tenant(mock_tenant_1):
            self.assertEqual(get_current_tenant(), mock_tenant_1)

            with use_tenant(mock_tenant_2):
                self.assertEqual(get_current_tenant(), mock_tenant_2)

            self.assertEqual(get_current_tenant(), mock_tenant_1)

        self.assertIsNone(get_current_tenant(), "O tenant deveria ser None apos sair de todos os contextos.")


class TenantRouterTests(TestCase):
    """
    Testa a logica de decisao do TenantRouter em memoria, sem acessar o banco.
    """

    def setUp(self):
        self.router = TenantRouter()
        self.mock_tenant = Mock()
        self.mock_tenant.db_name = "db_do_tenant_mock"
        self.mock_tenant.db_user = "tenant_user"
        self.mock_tenant.db_password = "tenant_pass"
        self.mock_tenant.db_host = "localhost"
        self.mock_tenant.db_port = "3306"

    def tearDown(self):
        set_current_tenant(None)

    def test_global_app_models_route_to_default(self):
        self.assertEqual(self.router.db_for_read(Tenant), 'default')
        self.assertEqual(self.router.db_for_write(Tenant), 'default')

        with use_tenant(self.mock_tenant):
            self.assertEqual(self.router.db_for_read(Tenant), 'default')
            self.assertEqual(self.router.db_for_write(Tenant), 'default')

    def test_tenant_app_models_route_to_tenant_alias(self):
        with use_tenant(self.mock_tenant):
            self.assertEqual(self.router.db_for_read(User), self.router.tenant_alias)
            self.assertEqual(self.router.db_for_write(User), self.router.tenant_alias)
            self.assertEqual(self.router.db_for_read(Group), self.router.tenant_alias)
            self.assertEqual(self.router.db_for_write(Group), self.router.tenant_alias)

    def test_tenant_app_models_route_to_default_when_no_tenant(self):
        set_current_tenant(None)
        self.assertEqual(self.router.db_for_read(User), 'default')
        self.assertEqual(self.router.db_for_write(User), 'default')
        self.assertEqual(self.router.db_for_read(Group), 'default')
        self.assertEqual(self.router.db_for_write(Group), 'default')

    def test_allow_migrate_logic(self):
        # Apps globais/de controle so podem migrar no 'default'.
        self.assertTrue(self.router.allow_migrate('default', 'control'))
        self.assertFalse(self.router.allow_migrate('db_de_tenant', 'control'))

        # Apps tenantizadas podem migrar no default (tenant mestre)
        # e tambem nos bancos dos tenants.
        self.assertTrue(self.router.allow_migrate('default', 'auth'))
        self.assertTrue(self.router.allow_migrate('default', 'accounts'))
        self.assertTrue(self.router.allow_migrate('default', 'empresas'))
        self.assertTrue(self.router.allow_migrate('db_de_tenant', 'auth'))
        self.assertTrue(self.router.allow_migrate('db_de_tenant', 'accounts'))
        self.assertTrue(self.router.allow_migrate('db_de_tenant', 'empresas'))

class ControlSecurityTests(DjangoTestCase):
    def test_ping_sem_login_redireciona_para_login(self):
        response = self.client.get(reverse('control:ping'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_ping_com_login_retorna_200(self):
        user = get_user_model().objects.create_user(username='user_ping', password='secret123')
        self.client.force_login(user)
        response = self.client.get(reverse('control:ping'))
        self.assertEqual(response.status_code, 200)
