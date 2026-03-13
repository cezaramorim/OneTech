from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class EmpresasSecurityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='user_empresas_sem_perm',
            password='secret123',
        )
        self.client.force_login(self.user)

    def test_lista_empresas_sem_permissao_retorna_403(self):
        response = self.client.get(reverse('empresas:lista_empresas'))
        self.assertEqual(response.status_code, 403)

    def test_lista_categorias_sem_permissao_retorna_403(self):
        response = self.client.get(reverse('empresas:lista_categorias'))
        self.assertEqual(response.status_code, 403)

class EmpresasApiSecurityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='user_empresas_api_sem_perm',
            password='secret123',
        )
        self.client.force_login(self.user)

    def test_fornecedores_api_sem_permissao_retorna_403(self):
        response = self.client.get('/empresas/api/v1/fornecedores/')
        self.assertEqual(response.status_code, 403)

    def test_cadastrar_categoria_sem_permissao_retorna_403_json_com_code(self):
        response = self.client.get(
            reverse('empresas:cadastrar_categoria'),
            HTTP_ACCEPT='application/json',
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json().get('code'), 'permission_denied')

    def test_cadastrar_empresa_sem_permissao_retorna_403_json_com_code(self):
        response = self.client.get(
            reverse('empresas:cadastrar_empresa'),
            HTTP_ACCEPT='application/json',
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json().get('code'), 'permission_denied')