from django.contrib.auth import get_user_model
from django.test import TestCase


class ProducaoApiSecurityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='producao_user_sem_perm',
            password='secret123',
        )

    def test_arracoamento_sugestoes_anon_redireciona_login(self):
        response = self.client.get('/producao/api/arracoamento/sugestoes/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_arracoamento_sugestoes_autenticado_sem_perm_retorna_403(self):
        self.client.force_login(self.user)
        response = self.client.get('/producao/api/arracoamento/sugestoes/')
        self.assertEqual(response.status_code, 403)

    def test_ambiente_get_autenticado_sem_perm_retorna_403(self):
        self.client.force_login(self.user)
        response = self.client.get('/producao/api/ambiente/')
        self.assertEqual(response.status_code, 403)

    def test_arracoamento_aprovar_autenticado_sem_perm_retorna_403(self):
        self.client.force_login(self.user)
        response = self.client.post(
            '/producao/api/arracoamento/aprovar/',
            data='{"ids": [1]}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)
