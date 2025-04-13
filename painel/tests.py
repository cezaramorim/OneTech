from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

class PainelViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='teste',
            password='senha123',
            email='teste@example.com'
        )

    def test_painel_view_com_login(self):
        self.client.login(username='teste', password='senha123')
        response = self.client.get(reverse('painel:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'base.html')
    
    def test_painel_view_sem_login(self):
        response = self.client.get(reverse('painel:home'))
        self.assertEqual(response.status_code, 302)  # redireciona para login
