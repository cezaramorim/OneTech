from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class RelatoriosSecurityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='user_relatorios_sem_perm',
            password='secret123',
        )
        self.client.force_login(self.user)

    def test_notas_entradas_sem_permissao_retorna_403(self):
        response = self.client.get(reverse('relatorios:notas_entradas'))
        self.assertEqual(response.status_code, 403)

    def test_api_notas_entradas_sem_permissao_retorna_403(self):
        response = self.client.get(reverse('relatorios:api_notas_entradas'))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json().get('code'), 'permission_denied')


class RelatoriosApiAuthContractTests(TestCase):
    def test_api_notas_entradas_sem_login_retorna_not_authenticated(self):
        response = self.client.get(reverse('relatorios:api_notas_entradas'))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json().get('code'), 'not_authenticated')
