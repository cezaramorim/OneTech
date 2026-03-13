from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import RequestFactory, TestCase, override_settings

from common.access_matrix import ROUTE_PERMISSION_MATRIX
from common.menu_config import MENU_ITEMS
from common.security_audit import log_permission_denied


class MenuPermissionConsistencyTests(TestCase):
    def _iter_items(self, items, trail=''):
        for item in items:
            name = item.get('name', '?')
            current = f"{trail} > {name}" if trail else name
            yield current, item
            children = item.get('children') or []
            if children:
                yield from self._iter_items(children, current)

    def test_menu_links_alinhados_com_matriz(self):
        problems = []
        for path, item in self._iter_items(MENU_ITEMS):
            url_name = item.get('url_name')
            if not url_name or url_name == '#':
                continue

            is_exception = item.get('staff_only') or item.get('superuser_only')
            menu_perms = tuple(item.get('required_perms') or ())
            matrix_perms = tuple(ROUTE_PERMISSION_MATRIX.get(url_name, ()))

            if url_name not in ROUTE_PERMISSION_MATRIX:
                problems.append(f"{path} ({url_name}) ausente na matriz")
                continue

            if menu_perms != matrix_perms:
                problems.append(f"{path} ({url_name}) divergente: menu={menu_perms} matriz={matrix_perms}")
                continue

            if not menu_perms and not is_exception:
                problems.append(f"{path} ({url_name}) sem required_perms")

        self.assertEqual(
            problems,
            [],
            msg='Inconsistencias menu x matriz:\n' + '\n'.join(problems),
        )


class AccessMatrixCommandTests(TestCase):
    def test_management_command_auditar_matriz_acesso_executa_com_sucesso(self):
        # Deve concluir sem excecao quando menu e matriz estao consistentes.
        call_command('auditar_matriz_acesso')

    def test_management_command_validar_baseline_seguranca_executa_com_sucesso(self):
        # Deve concluir sem excecao com a baseline atual de settings.
        call_command('validar_baseline_seguranca')

    @override_settings(
        USE_HTTPS=False,
        SESSION_COOKIE_SECURE=False,
        CSRF_COOKIE_SECURE=False,
        SECURE_SSL_REDIRECT=False,
        SECURE_HSTS_SECONDS=0,
        SECURE_HSTS_INCLUDE_SUBDOMAINS=False,
        SECURE_HSTS_PRELOAD=False,
    )
    def test_management_command_validar_baseline_seguranca_strict_falha_sem_flags_https(self):
        with self.assertRaises(SystemExit):
            call_command('validar_baseline_seguranca', '--strict')

    @override_settings(
        USE_HTTPS=True,
        SESSION_COOKIE_SECURE=True,
        CSRF_COOKIE_SECURE=True,
        SECURE_SSL_REDIRECT=True,
        SECURE_HSTS_SECONDS=31536000,
        SECURE_HSTS_INCLUDE_SUBDOMAINS=True,
        SECURE_HSTS_PRELOAD=True,
    )
    def test_management_command_validar_baseline_seguranca_strict_aprova_com_flags_https(self):
        call_command('validar_baseline_seguranca', '--strict')


class SecurityAuditTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_log_permission_denied_emite_evento_com_payload_minimo(self):
        user = get_user_model().objects.create_user(username='audit_user', password='secret123')
        request = self.factory.get('/fiscal/cfops/', HTTP_HOST='127.0.0.1')
        request.user = user
        request.tenant = None

        with self.assertLogs('security.authz', level='WARNING') as captured:
            log_permission_denied(request, code='permission_denied', detail='fiscal.view_cfop')

        self.assertTrue(captured.output)
        self.assertIn('AUTHZ_DENIED', captured.output[0])
        self.assertIn('permission_denied', captured.output[0])

class PathPermissionMatrixContractTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='matrix_user_sem_perm',
            password='secret123',
        )

    def test_api_notas_entradas_anon_retorna_not_authenticated(self):
        response = self.client.get('/api/v1/notas-entradas/')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json().get('code'), 'not_authenticated')

    def test_api_notas_entradas_autenticado_sem_perm_retorna_permission_denied(self):
        self.client.force_login(self.user)
        response = self.client.get('/api/v1/notas-entradas/')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json().get('code'), 'permission_denied')

    def test_api_itens_nota_autenticado_sem_perm_retorna_permission_denied(self):
        self.client.force_login(self.user)
        response = self.client.get('/api/v1/nota-fiscal/itens/')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json().get('code'), 'permission_denied')

    def test_api_fornecedores_autenticado_sem_perm_retorna_permission_denied(self):
        self.client.force_login(self.user)
        response = self.client.get('/empresas/api/v1/fornecedores/')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json().get('code'), 'permission_denied')

    def test_ping_anon_redireciona_login(self):
        response = self.client.get('/gerenciamento/ping/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_ping_autenticado_retorna_200(self):
        self.client.force_login(self.user)
        response = self.client.get('/gerenciamento/ping/')
        self.assertEqual(response.status_code, 200)

    def test_webhook_sefaz_sem_assinatura_retorna_401(self):
        response = self.client.post(
            '/integracao-nfe/webhook/sefaz/',
            data='{}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)
    def test_produtos_api_racoes_anon_redireciona_login(self):
        response = self.client.get('/produtos/api/racoes/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_produtos_api_racoes_autenticado_retorna_200(self):
        self.client.force_login(self.user)
        response = self.client.get('/produtos/api/racoes/')
        self.assertEqual(response.status_code, 200)

    def test_produtos_buscar_ncm_anon_redireciona_login(self):
        response = self.client.get('/produtos/buscar-ncm/', {'search': '0101'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_produtos_buscar_ncm_autenticado_retorna_200(self):
        self.client.force_login(self.user)
        response = self.client.get('/produtos/buscar-ncm/', {'search': '0101'})
        self.assertEqual(response.status_code, 200)
