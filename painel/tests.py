from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse


class PainelPermissionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='user_painel_sem_perm',
            password='secret123',
        )

    def test_home_sem_permissao_retorna_403(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('painel:home'))
        self.assertEqual(response.status_code, 403)

    def test_home_ajax_sem_permissao_retorna_403_json(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('painel:home'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json().get('code'), 'permission_denied')

    def test_home_com_permissao_retorna_200(self):
        permission = Permission.objects.get(codename='view_dashboard')
        self.user.user_permissions.add(permission)
        self.client.force_login(self.user)
        response = self.client.get(reverse('painel:home'))
        self.assertEqual(response.status_code, 200)
