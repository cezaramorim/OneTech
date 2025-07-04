from django.test import TestCase
from .models import Cfop

class CfopModelTest(TestCase):
    def setUp(self):
        self.cfop = Cfop.objects.create(
            codigo='5102',
            descricao='Venda de mercadoria adquirida ou recebida de terceiros',
            categoria='Venda'
        )

    def test_cfop_creation(self):
        """Testa se o objeto Cfop é criado corretamente."""
        self.assertEqual(self.cfop.codigo, '5102')
        self.assertEqual(self.cfop.descricao, 'Venda de mercadoria adquirida ou recebida de terceiros')
        self.assertEqual(self.cfop.categoria, 'Venda')
        self.assertEqual(str(self.cfop), '5102 - Venda de mercadoria adquirida ou recebida de terceiros')

import pandas as pd
from io import BytesIO
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from fiscal.models import Cfop

class UploadCfopViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.admin_user = self.User.objects.create_user(
            username='testadmin',
            password='admin123',
            is_staff=True
        )
        # Adiciona a permissão para adicionar CFOP
        content_type = ContentType.objects.get_for_model(Cfop)
        permission = Permission.objects.get(
            codename='add_cfop',
            content_type=content_type,
        )
        self.admin_user.user_permissions.add(permission)
        self.client.login(username='testadmin', password='admin123')

        # Cria um arquivo .xlsx em memória para o teste
        self.excel_file = self.create_test_excel_file()

    def create_test_excel_file(self):
        """Cria um arquivo Excel (.xlsx) em memória para os testes."""
        df = pd.DataFrame({
            'codigo': ['1101', '1102'],
            'descricao': ['Compra para industrialização', 'Compra para comercialização'],
            'categoria': ['Entrada', 'Entrada']
        })
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='CFOPs')
        output.seek(0)
        output.name = 'test_cfops.xlsx'  # Adiciona um nome ao arquivo
        return output

    def test_upload_cfop_success(self):
        """Testa o upload bem-sucedido de um arquivo .xlsx de CFOPs."""
        url = reverse('fiscal:import_fiscal_data')
        response = self.client.post(url, {
            'excel_file': self.excel_file,
            'import_type': 'cfop'
        }, format='multipart')

        self.assertEqual(response.status_code, 302) # Redirecionamento após sucesso
        self.assertTrue(Cfop.objects.filter(codigo='1101').exists())
        self.assertTrue(Cfop.objects.filter(codigo='1102').exists())
        self.assertEqual(Cfop.objects.count(), 2)

    def test_upload_cfop_unauthenticated(self):
        """Testa que um usuário não autenticado é redirecionado para a página de login."""
        self.client.logout()
        url = reverse('fiscal:import_fiscal_data')
        response = self.client.post(url, {
            'excel_file': self.excel_file,
            'import_type': 'cfop'
        }, format='multipart')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url) # URL de login padrão do Django
        self.assertFalse(Cfop.objects.exists())

    def test_upload_cfop_no_permission(self):
        """Testa que um usuário sem permissão não pode fazer o upload."""
        # Cria um novo usuário sem a permissão de adicionar CFOP
        no_perm_user = self.User.objects.create_user(username='noperm', password='noperm123')
        self.client.login(username='noperm', password='noperm123')

        url = reverse('fiscal:import_fiscal_data')
        response = self.client.post(url, {
            'excel_file': self.excel_file,
            'import_type': 'cfop'
        }, format='multipart')

        # Como a view agora tem verificação de permissão, esperamos um 403 Forbidden.
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Cfop.objects.exists())
