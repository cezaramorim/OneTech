from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import RequestFactory, TestCase

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