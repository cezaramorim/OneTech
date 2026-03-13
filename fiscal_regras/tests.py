from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class FiscalRegrasSecurityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='user_fiscal_regras_sem_perm',
            password='secret123',
        )
        self.client.force_login(self.user)

    def test_lista_regras_sem_permissao_retorna_403(self):
        response = self.client.get(reverse('fiscal_regras:regra_icms_list'))
        self.assertEqual(response.status_code, 403)

    def test_resolver_api_sem_permissao_retorna_403(self):
        response = self.client.get(reverse('fiscal_regras:resolver_aliquota_icms_api'))
        self.assertEqual(response.status_code, 403)
