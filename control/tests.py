import json
import time
import hmac
import hashlib
from unittest import TestCase
from unittest.mock import Mock, patch
import subprocess

from control.db_router import TenantRouter
from control.utils import get_current_tenant, set_current_tenant, use_tenant
from control.models import SecurityAuditEvent, Tenant
from accounts.models import User
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.http import HttpResponse
from django.test import RequestFactory, TestCase as DjangoTestCase, override_settings
from django.urls import reverse
from django.core.cache import cache


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


@override_settings(ALLOWED_HOSTS=['testserver', 'ativo.localhost', 'inativo.localhost', 'bloqueado.localhost', 'quarentena.localhost'])
class TenantMiddlewareTests(DjangoTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _build_tenant(self, dominio='tenant.localhost', ativo=True):
        return Tenant.objects.create(
            nome='Tenant Teste',
            slug=dominio.replace('.', '-'),
            dominio=dominio,
            db_name=f"db_{dominio.replace('.', '_')}",
            db_user='tenant_user',
            db_password='tenant_pass',
            db_host='127.0.0.1',
            db_port='3306',
            razao_social='Tenant Teste LTDA',
            nome_fantasia='Tenant Teste',
            cnpj=f'00.000.000/0001-{Tenant.objects.count() + 10:02d}',
            ativo=ativo,
        )

    def tearDown(self):
        set_current_tenant(None)
        super().tearDown()

    def test_resolve_tenant_por_host_ativo(self):
        tenant = self._build_tenant(dominio='ativo.localhost', ativo=True)

        middleware = __import__('control.middleware', fromlist=['TenantMiddleware']).TenantMiddleware(
            lambda request: HttpResponse('ok')
        )
        request = self.factory.get('/painel/', HTTP_HOST='ativo.localhost')

        response = middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(request.tenant)
        self.assertEqual(request.tenant.id, tenant.id)
        self.assertEqual(get_current_tenant().id, tenant.id)

    def test_nao_resolve_tenant_inativo(self):
        self._build_tenant(dominio='inativo.localhost', ativo=False)

        middleware = __import__('control.middleware', fromlist=['TenantMiddleware']).TenantMiddleware(
            lambda request: HttpResponse('ok')
        )
        request = self.factory.get('/painel/', HTTP_HOST='inativo.localhost')

        response = middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(request.tenant)
        self.assertIsNone(get_current_tenant())

    def test_admin_bloqueado_em_contexto_tenant(self):
        self._build_tenant(dominio='bloqueado.localhost', ativo=True)

        middleware = __import__('control.middleware', fromlist=['TenantMiddleware']).TenantMiddleware(
            lambda request: HttpResponse('ok')
        )
        request = self.factory.get('/admin/', HTTP_HOST='bloqueado.localhost')

        response = middleware(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/painel/?admin_restrito=1')


    def test_tenant_quarentena_bloqueia_post(self):
        tenant = self._build_tenant(dominio='quarentena.localhost', ativo=True)
        cache.set(f'security:tenant-quarantine:{tenant.slug}', {'active': True}, timeout=None)

        middleware = __import__('control.middleware', fromlist=['TenantMiddleware']).TenantMiddleware(
            lambda request: HttpResponse('ok')
        )
        request = self.factory.post('/produtos/novo/', HTTP_HOST='quarentena.localhost', HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        response = middleware(request)

        self.assertEqual(response.status_code, 423)
        cache.delete(f'security:tenant-quarantine:{tenant.slug}')
class SecurityCenterTests(DjangoTestCase):
    def setUp(self):
        self.superuser = get_user_model().objects.create_superuser(
            username='sec_admin',
            email='sec_admin@example.com',
            password='secret123',
        )
        self.common_user = get_user_model().objects.create_user(
            username='sec_user',
            password='secret123',
        )

    def test_security_center_superuser_retorna_200(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('control:central_seguranca'))
        self.assertEqual(response.status_code, 200)

    def test_security_center_usuario_comum_redireciona(self):
        self.client.force_login(self.common_user)
        response = self.client.get(reverse('control:central_seguranca'))
        self.assertEqual(response.status_code, 302)

    def test_security_run_audit_usuario_comum_redireciona(self):
        self.client.force_login(self.common_user)
        response = self.client.post(
            reverse('control:security_run_audit'),
            data='{"mode":"normal"}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 302)

    def test_security_force_logout_superuser(self):
        from django.contrib.sessions.backends.db import SessionStore
        from django.contrib.sessions.models import Session

        session = SessionStore()
        session['_auth_user_id'] = str(self.common_user.id)
        session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
        session['_auth_user_hash'] = self.common_user.get_session_auth_hash()
        session.save()

        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse('control:security_force_logout_user'),
            data=json.dumps({'user_id': self.common_user.id, 'confirm_username': self.common_user.username}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Session.objects.filter(session_key=session.session_key).exists())

    @patch('control.views.call_command')
    def test_security_run_audit_superuser_persiste_evento(self, mock_call_command):
        mock_call_command.return_value = None

        self.client.force_login(self.superuser)
        before = SecurityAuditEvent.objects.count()
        response = self.client.post(
            reverse('control:security_run_audit'),
            data=json.dumps({'mode': 'normal'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get('success'))
        self.assertEqual(SecurityAuditEvent.objects.count(), before + 1)

        event = SecurityAuditEvent.objects.order_by('-id').first()
        self.assertIsNotNone(event)
        self.assertEqual(event.code, 'run_security_audit')
        self.assertEqual(event.event_type, SecurityAuditEvent.EVENT_SYSTEM)

    @patch('control.views.call_command', side_effect=SystemExit(1))
    def test_security_run_audit_strict_reprovada_retorna_200_com_saida(self, _mock_call_command):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse('control:security_run_audit'),
            data=json.dumps({'mode': 'strict'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload.get('success'))
        self.assertEqual(payload.get('mode'), 'strict')
        self.assertIn('reprovada', payload.get('message', '').lower())

    def test_security_event_filtro_por_texto_e_tipo(self):
        SecurityAuditEvent.objects.create(
            event_type=SecurityAuditEvent.EVENT_SYSTEM,
            code='auth_login_success',
            detail='Login realizado',
            method='POST',
            path='/accounts/login/',
            host='127.0.0.1',
            ip_address='127.0.0.1',
            user_id=self.superuser.id,
            metadata={'request_username': self.superuser.username},
        )
        SecurityAuditEvent.objects.create(
            event_type=SecurityAuditEvent.EVENT_AUTHZ_DENIED,
            code='permission_denied',
            detail='Bloqueado',
            method='GET',
            path='/fiscal/cfops/',
            host='127.0.0.1',
            ip_address='127.0.0.1',
            user_id=self.common_user.id,
            metadata={'request_username': self.common_user.username},
        )

        self.client.force_login(self.superuser)
        response = self.client.get(reverse('control:central_seguranca'), {'q': 'permission', 'tipo': 'AUTHZ_DENIED'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'permission_denied')
        self.assertNotContains(response, 'auth_login_success')

    def test_security_signals_login_logout_failed_persistem_eventos(self):
        factory = RequestFactory()

        req_login = factory.post('/accounts/login/')
        req_login.user = self.superuser
        user_logged_in.send(sender=get_user_model(), request=req_login, user=self.superuser)

        req_logout = factory.post('/accounts/logout/')
        req_logout.user = self.superuser
        user_logged_out.send(sender=get_user_model(), request=req_logout, user=self.superuser)

        req_failed = factory.post('/accounts/login/')
        req_failed.user = self.common_user
        user_login_failed.send(
            sender=get_user_model(),
            credentials={'username': 'usuario.invalido'},
            request=req_failed,
        )

        codes = list(SecurityAuditEvent.objects.values_list('code', flat=True))
        self.assertIn('auth_login_success', codes)
        self.assertIn('auth_logout', codes)
        self.assertIn('auth_login_failed', codes)


    def test_security_export_csv_aplica_filtro(self):
        SecurityAuditEvent.objects.create(
            event_type=SecurityAuditEvent.EVENT_SYSTEM,
            code='auth_login_success',
            detail='Login realizado',
            method='POST',
            path='/accounts/login/',
            host='127.0.0.1',
            ip_address='127.0.0.1',
            user_id=self.superuser.id,
            metadata={'request_username': self.superuser.username},
        )
        SecurityAuditEvent.objects.create(
            event_type=SecurityAuditEvent.EVENT_AUTHZ_DENIED,
            code='permission_denied',
            detail='Bloqueado',
            method='GET',
            path='/fiscal/cfops/',
            host='127.0.0.1',
            ip_address='127.0.0.1',
            user_id=self.common_user.id,
            metadata={'request_username': self.common_user.username},
        )

        self.client.force_login(self.superuser)
        response = self.client.get(
            reverse('control:security_export_events_csv'),
            {'q': 'permission', 'tipo': 'AUTHZ_DENIED'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response['Content-Type'])
        csv_text = response.content.decode('utf-8')
        self.assertIn('permission_denied', csv_text)
        self.assertNotIn('auth_login_success', csv_text)


    def test_security_center_stats_inclui_janelas_7d_30d(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('control:central_seguranca'))

        self.assertEqual(response.status_code, 200)
        stats = response.context['security_stats']
        self.assertIn('denied_24h', stats)
        self.assertIn('denied_7d', stats)
        self.assertIn('denied_30d', stats)


    def test_security_center_exibe_alerta_burst_por_ip(self):
        for _ in range(5):
            SecurityAuditEvent.objects.create(
                event_type=SecurityAuditEvent.EVENT_AUTHZ_DENIED,
                code='permission_denied',
                detail='Bloqueado',
                method='GET',
                path='/fiscal/cfops/',
                host='127.0.0.1',
                ip_address='10.10.10.10',
                user_id=self.common_user.id,
                metadata={'request_username': self.common_user.username},
            )

        self.client.force_login(self.superuser)
        response = self.client.get(reverse('control:central_seguranca'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '10.10.10.10')
        self.assertContains(response, '5')


    def test_security_center_exibe_alerta_endpoint_sensivel(self):
        for _ in range(3):
            SecurityAuditEvent.objects.create(
                event_type=SecurityAuditEvent.EVENT_AUTHZ_DENIED,
                code='permission_denied',
                detail='Bloqueado',
                method='GET',
                path='/admin/',
                host='127.0.0.1',
                ip_address='172.16.1.10',
                user_id=self.common_user.id,
                metadata={'request_username': self.common_user.username},
            )

        self.client.force_login(self.superuser)
        response = self.client.get(reverse('control:central_seguranca'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/admin/')
        self.assertContains(response, 'Endpoints Sensiveis (24h)')


    def test_security_center_exibe_top_origens(self):
        for _ in range(4):
            SecurityAuditEvent.objects.create(
                event_type=SecurityAuditEvent.EVENT_AUTHZ_DENIED,
                code='permission_denied',
                detail='Bloqueado',
                method='GET',
                path='/fiscal/cfops/',
                host='api.local',
                ip_address='192.168.0.10',
                user_id=self.common_user.id,
                metadata={'request_username': self.common_user.username},
            )

        self.client.force_login(self.superuser)
        response = self.client.get(reverse('control:central_seguranca'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Top Origens (24h)')
        self.assertContains(response, 'api.local')
        self.assertContains(response, '192.168.0.10')


    def test_security_center_exibe_risco_por_tenant(self):
        for _ in range(10):
            SecurityAuditEvent.objects.create(
                event_type=SecurityAuditEvent.EVENT_AUTHZ_DENIED,
                code='permission_denied',
                detail='Bloqueado',
                method='GET',
                path='/gerenciamento/tenants/',
                host='127.0.0.1',
                ip_address='10.0.0.2',
                tenant_slug='aquatech',
                user_id=self.common_user.id,
                metadata={'request_username': self.common_user.username},
            )

        self.client.force_login(self.superuser)
        response = self.client.get(reverse('control:central_seguranca'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Risco por Tenant (24h)')
        self.assertContains(response, 'aquatech')
        self.assertContains(response, 'MEDIO')


    def test_security_center_exibe_links_detalhar_alertas(self):
        for _ in range(5):
            SecurityAuditEvent.objects.create(
                event_type=SecurityAuditEvent.EVENT_AUTHZ_DENIED,
                code='permission_denied',
                detail='Bloqueado',
                method='GET',
                path='/admin/',
                host='api.local',
                ip_address='192.168.1.1',
                tenant_slug='aquatech',
                user_id=self.common_user.id,
                metadata={'request_username': self.common_user.username},
            )

        self.client.force_login(self.superuser)
        response = self.client.get(reverse('control:central_seguranca'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Detalhar')
        self.assertContains(response, 'tipo=AUTHZ_DENIED')


    def test_security_force_logout_requer_confirmacao_reforcada(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse('control:security_force_logout_user'),
            data=json.dumps({'user_id': self.common_user.id, 'confirm_username': 'errado'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Confirmacao reforcada invalida', response.json().get('message', ''))


    def test_security_center_exibe_historico_acoes_admin(self):
        SecurityAuditEvent.objects.create(
            event_type=SecurityAuditEvent.EVENT_SYSTEM,
            code='force_logout_user',
            detail='Teste de historico administrativo',
            method='POST',
            path='/gerenciamento/seguranca/encerrar-sessoes/',
            host='127.0.0.1',
            ip_address='127.0.0.1',
            user_id=self.superuser.id,
            metadata={'request_username': self.superuser.username},
        )

        self.client.force_login(self.superuser)
        response = self.client.get(reverse('control:central_seguranca'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Historico de Acoes Administrativas')
        self.assertContains(response, 'force_logout_user')


    def test_security_toggle_lock_usuario_comum_redireciona(self):
        self.client.force_login(self.common_user)
        response = self.client.post(
            reverse('control:security_toggle_user_lock'),
            data=json.dumps({'user_id': self.superuser.id, 'mode': 'lock', 'confirm_username': self.superuser.username}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 302)


    def test_security_toggle_lock_bloqueia_login_ate_desbloqueio(self):
        lock_key = f'security:user-lock:{self.common_user.id}'
        cache.delete(lock_key)

        self.client.force_login(self.superuser)
        lock_response = self.client.post(
            reverse('control:security_toggle_user_lock'),
            data=json.dumps({'user_id': self.common_user.id, 'mode': 'lock', 'minutes': 15, 'confirm_username': self.common_user.username}),
            content_type='application/json',
        )
        self.assertEqual(lock_response.status_code, 200)

        self.client.logout()
        blocked_login_response = self.client.post(
            reverse('accounts:login'),
            data={'username': self.common_user.username, 'password': 'secret123'},
        )
        self.assertEqual(blocked_login_response.status_code, 200)
        self.assertContains(blocked_login_response, 'Usuario temporariamente bloqueado')

        self.client.force_login(self.superuser)
        unlock_response = self.client.post(
            reverse('control:security_toggle_user_lock'),
            data=json.dumps({'user_id': self.common_user.id, 'mode': 'unlock', 'confirm_username': self.common_user.username}),
            content_type='application/json',
        )
        self.assertEqual(unlock_response.status_code, 200)
        self.assertIsNone(cache.get(lock_key))


    def test_security_toggle_tenant_quarantine_usuario_comum_redireciona(self):
        self.client.force_login(self.common_user)
        response = self.client.post(
            reverse('control:security_toggle_tenant_quarantine'),
            data=json.dumps({'tenant_slug': 'qualquer', 'mode': 'enable', 'confirm_slug': 'qualquer'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 302)


    def test_security_toggle_tenant_quarantine_superuser(self):
        tenant = Tenant.objects.create(
            nome='Tenant Quarentena',
            slug='tenant-quarentena',
            dominio='tenant-quarentena.localhost',
            db_name='db_tenant_quarentena',
            db_user='tenant_user',
            db_password='tenant_pass',
            db_host='127.0.0.1',
            db_port='3306',
            razao_social='Tenant Quarentena LTDA',
            nome_fantasia='Tenant Quarentena',
            cnpj='00.000.000/0001-99',
            ativo=True,
        )

        key = f'security:tenant-quarantine:{tenant.slug}'
        cache.delete(key)

        self.client.force_login(self.superuser)
        enable = self.client.post(
            reverse('control:security_toggle_tenant_quarantine'),
            data=json.dumps({'tenant_slug': tenant.slug, 'mode': 'enable', 'confirm_slug': tenant.slug}),
            content_type='application/json',
        )
        self.assertEqual(enable.status_code, 200)
        self.assertIsNotNone(cache.get(key))

        disable = self.client.post(
            reverse('control:security_toggle_tenant_quarantine'),
            data=json.dumps({'tenant_slug': tenant.slug, 'mode': 'disable', 'confirm_slug': tenant.slug}),
            content_type='application/json',
        )
        self.assertEqual(disable.status_code, 200)
        self.assertIsNone(cache.get(key))


    def test_security_run_dependency_audit_usuario_comum_redireciona(self):
        self.client.force_login(self.common_user)
        response = self.client.post(
            reverse('control:security_run_dependency_audit'),
            data='{}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 302)


    @patch('control.views.subprocess.run')
    def test_security_run_dependency_audit_superuser_ok(self, mock_run):
        mock_run.return_value = Mock(
            returncode=1,
            stdout='{"dependencies": [{"name": "pkg-a", "vulns": [{"id": "CVE-1"}]}]}',
            stderr=''
        )

        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse('control:security_run_dependency_audit'),
            data='{}',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get('success'))
        self.assertEqual(payload.get('snapshot', {}).get('vulnerable_count'), 1)


    @patch('control.views.subprocess.run', side_effect=subprocess.TimeoutExpired(cmd='pip_audit', timeout=180))
    def test_security_run_dependency_audit_timeout(self, _mock_run):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse('control:security_run_dependency_audit'),
            data='{}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 504)

    @patch('control.views.call_command')
    def test_security_run_matrix_audit_superuser_ok(self, mock_call_command):
        mock_call_command.return_value = None

        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse('control:security_run_matrix_audit'),
            data='{}',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get('success'))
        self.assertIn('summary', payload)


    def test_security_export_consolidated_json_e_csv(self):
        self.client.force_login(self.superuser)

        response_json = self.client.get(reverse('control:security_export_consolidated'), {'format': 'json'})
        self.assertEqual(response_json.status_code, 200)
        self.assertTrue(response_json.json().get('success'))

        response_csv = self.client.get(reverse('control:security_export_consolidated'), {'format': 'csv'})
        self.assertEqual(response_csv.status_code, 200)
        self.assertIn('text/csv', response_csv['Content-Type'])


    def test_security_siem_events_endpoint_retorna_eventos(self):
        SecurityAuditEvent.objects.create(
            event_type=SecurityAuditEvent.EVENT_SYSTEM,
            code='test_siem_event',
            detail='Evento SIEM',
            method='GET',
            path='/painel/',
            host='127.0.0.1',
            ip_address='127.0.0.1',
            user_id=self.superuser.id,
            metadata={'request_username': self.superuser.username},
        )

        self.client.force_login(self.superuser)
        response = self.client.get(reverse('control:security_siem_events'), {'since_minutes': 120, 'limit': 50})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get('success'))
        self.assertGreaterEqual(payload.get('count'), 1)


    @override_settings(SECURITY_SIEM_TOKEN='token-siem-123')
    def test_security_siem_events_endpoint_aceita_token_tecnico(self):
        SecurityAuditEvent.objects.create(
            event_type=SecurityAuditEvent.EVENT_SYSTEM,
            code='token_siem_event',
            detail='Evento SIEM token',
            method='GET',
            path='/painel/',
            host='127.0.0.1',
            ip_address='127.0.0.1',
            user_id=self.superuser.id,
            metadata={'request_username': self.superuser.username},
        )

        response = self.client.get(
            reverse('control:security_siem_events'),
            {'since_minutes': 60, 'limit': 10},
            HTTP_X_SIEM_TOKEN='token-siem-123',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get('success'))
        self.assertEqual(payload.get('actor'), 'token')

    @override_settings(SECURITY_SIEM_TOKEN='token-siem-123')
    def test_security_siem_events_endpoint_rejeita_token_invalido(self):
        response = self.client.get(
            reverse('control:security_siem_events'),
            {'since_minutes': 60, 'limit': 10},
            HTTP_X_SIEM_TOKEN='token-invalido',
        )
        self.assertEqual(response.status_code, 401)
        payload = response.json()
        self.assertFalse(payload.get('success'))

    @override_settings(
        SECURITY_SIEM_TOKEN='token-siem-123',
        SECURITY_SIEM_REQUIRE_HMAC=True,
        SECURITY_SIEM_HMAC_SECRET='segredo-hmac',
    )
    def test_security_siem_events_endpoint_rejeita_hmac_invalido(self):
        response = self.client.get(
            reverse('control:security_siem_events'),
            {'since_minutes': 60, 'limit': 10},
            HTTP_X_SIEM_TOKEN='token-siem-123',
            HTTP_X_SIEM_TIMESTAMP=str(int(time.time())),
            HTTP_X_SIEM_SIGNATURE='assinatura-invalida',
        )
        self.assertEqual(response.status_code, 401)
        payload = response.json()
        self.assertFalse(payload.get('success'))

    @override_settings(
        SECURITY_SIEM_TOKEN='token-siem-123',
        SECURITY_SIEM_REQUIRE_HMAC=True,
        SECURITY_SIEM_HMAC_SECRET='segredo-hmac',
    )
    def test_security_siem_events_endpoint_aceita_hmac_valido(self):
        query = 'since_minutes=60&limit=10'
        path = f"{reverse('control:security_siem_events')}?{query}"
        ts = str(int(time.time()))
        signature_base = f'{ts}.{path}'
        signature = hmac.new(
            b'segredo-hmac',
            signature_base.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

        response = self.client.get(
            reverse('control:security_siem_events'),
            {'since_minutes': 60, 'limit': 10},
            HTTP_X_SIEM_TOKEN='token-siem-123',
            HTTP_X_SIEM_TIMESTAMP=ts,
            HTTP_X_SIEM_SIGNATURE=signature,
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get('success'))

    @override_settings(
        SECURITY_SIEM_TOKEN='token-siem-123',
        SECURITY_SIEM_RATE_LIMIT_PER_MINUTE=1,
    )
    def test_security_siem_events_endpoint_aplica_rate_limit(self):
        url = reverse('control:security_siem_events')
        remote_ip = '198.51.100.77'
        response_first = self.client.get(
            url,
            {'since_minutes': 60, 'limit': 10},
            HTTP_X_SIEM_TOKEN='token-siem-123',
            REMOTE_ADDR=remote_ip,
        )
        self.assertEqual(response_first.status_code, 200)

        response_second = self.client.get(
            url,
            {'since_minutes': 60, 'limit': 10},
            HTTP_X_SIEM_TOKEN='token-siem-123',
            REMOTE_ADDR=remote_ip,
        )
        self.assertEqual(response_second.status_code, 429)

    @patch('control.views.call_command')
    def test_security_run_audit_strict_atualiza_snapshot_baseline(self, mock_call_command):
        mock_call_command.return_value = None

        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse('control:security_run_audit'),
            data=json.dumps({'mode': 'strict'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('baseline_snapshot', payload)
        self.assertIsNotNone(payload.get('baseline_snapshot'))

