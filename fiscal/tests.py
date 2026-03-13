from io import BytesIO
import shutil
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client, TestCase
from django.urls import reverse

from fiscal.fiscal_services import inspect_duplicates, load_local_data, save_local_data, update_local_data_from_excel
from fiscal.models import Cfop, NaturezaOperacao


class FiscalLocalFileIsolationMixin:
    def setUp(self):
        super().setUp()
        self._temp_root = Path.cwd() / '.tmp_fiscal_tests'
        self._temp_root.mkdir(exist_ok=True)
        self._temp_path = self._temp_root / self.__class__.__name__
        self._temp_path.mkdir(exist_ok=True)
        self._path_patcher = patch('fiscal.fiscal_services._get_json_path', side_effect=self._get_json_path)
        self._path_patcher.start()

    def tearDown(self):
        self._path_patcher.stop()
        shutil.rmtree(self._temp_path, ignore_errors=True)
        if hasattr(self, '_temp_root') and self._temp_root.exists() and not any(self._temp_root.iterdir()):
            self._temp_root.rmdir()
        super().tearDown()

    def _get_json_path(self, data_type):
        file_name = 'cfop.json' if data_type == 'cfop' else 'natureza_operacao.json'
        return self._temp_path / file_name


class CfopModelTest(TestCase):
    def test_cfop_save_normalizes_codigo(self):
        cfop = Cfop.objects.create(codigo='51.02', descricao='  Venda de mercadoria  ', categoria=' Saida ')

        self.assertEqual(cfop.codigo, '5102')
        self.assertEqual(cfop.descricao, 'Venda de mercadoria')
        self.assertEqual(cfop.categoria, 'Saida')


class NaturezaOperacaoModelTest(TestCase):
    def test_natureza_save_normalizes_fields(self):
        natureza = NaturezaOperacao.objects.create(codigo=' venda ', descricao='  Venda de Mercadoria  ', observacoes='  padrao  ')

        self.assertEqual(natureza.codigo, 'VENDA')
        self.assertEqual(natureza.descricao, 'Venda de Mercadoria')
        self.assertEqual(natureza.observacoes, 'padrao')


class FiscalLocalDataTests(FiscalLocalFileIsolationMixin, TestCase):
    def create_excel(self, rows):
        output = BytesIO()
        df = pd.DataFrame(rows)
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Dados')
        output.seek(0)
        output.name = 'dados.xlsx'
        return output

    def test_update_local_data_from_excel_for_cfop(self):
        excel = self.create_excel([
            {'codigo': '1101', 'descricao': 'Compra', 'categoria': 'Entrada'},
            {'codigo': '5102', 'descricao': 'Venda', 'categoria': 'Saida'},
        ])

        payload = update_local_data_from_excel(excel, 'cfop')

        self.assertEqual(payload['metadata']['item_count'], 2)
        saved = load_local_data('cfop')
        self.assertEqual(saved['items'][0]['codigo'], '1101')

    def test_inspect_duplicates_for_natureza(self):
        NaturezaOperacao.objects.create(codigo=None, descricao='Venda de Mercadoria')
        NaturezaOperacao.objects.create(codigo='', descricao='  Venda de Mercadoria  ')

        summary = inspect_duplicates('natureza_operacao')

        self.assertEqual(summary['group_count'], 1)


class FiscalImportFlowTests(FiscalLocalFileIsolationMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='fiscaladmin', password='admin123')
        cfop_ct = ContentType.objects.get_for_model(Cfop)
        natureza_ct = ContentType.objects.get_for_model(NaturezaOperacao)
        self.user.user_permissions.add(Permission.objects.get(codename='add_cfop', content_type=cfop_ct))
        self.user.user_permissions.add(Permission.objects.get(codename='view_cfop', content_type=cfop_ct))
        self.user.user_permissions.add(Permission.objects.get(codename='delete_cfop', content_type=cfop_ct))
        self.user.user_permissions.add(Permission.objects.get(codename='add_naturezaoperacao', content_type=natureza_ct))
        self.user.user_permissions.add(Permission.objects.get(codename='view_naturezaoperacao', content_type=natureza_ct))
        self.client.login(username='fiscaladmin', password='admin123')

    def create_excel(self):
        output = BytesIO()
        df = pd.DataFrame({
            'codigo': ['1101', '1102'],
            'descricao': ['Compra para industrializacao', 'Compra para comercializacao'],
            'categoria': ['Entrada', 'Entrada'],
        })
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='CFOPs')
        output.seek(0)
        output.name = 'cfop.xlsx'
        return output

    def test_upload_excel_updates_local_base_only(self):
        response = self.client.post(reverse('fiscal:import_fiscal_data'), {
            'excel_file': self.create_excel(),
            'import_type': 'cfop',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Cfop.objects.count(), 0)
        local = load_local_data('cfop')
        self.assertEqual(local['metadata']['item_count'], 2)

    def test_import_local_view_imports_records_to_db(self):
        save_local_data('cfop', [
            {'codigo': '1101', 'descricao': 'Compra', 'categoria': 'Entrada'},
            {'codigo': '1102', 'descricao': 'Compra 2', 'categoria': 'Entrada'},
        ], source='test')

        response = self.client.post(reverse('fiscal:import_fiscal_local'), {'import_type': 'cfop'})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Cfop.objects.filter(codigo='1101').exists())
        self.assertEqual(Cfop.objects.count(), 2)


class FiscalPermissionViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='viewer', password='viewer123')
        self.cfop = Cfop.objects.create(codigo='5102', descricao='Venda', categoria='Saida')

    def test_cfop_list_requires_view_permission(self):
        self.client.login(username='viewer', password='viewer123')

        response = self.client.get(reverse('fiscal:cfop_list'))

        self.assertEqual(response.status_code, 403)

    def test_delete_cfop_requires_delete_permission(self):
        self.client.login(username='viewer', password='viewer123')

        response = self.client.post(
            reverse('fiscal:delete_fiscal_items'),
            data='{"ids": [%s], "item_type": "cfop"}' % self.cfop.pk,
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json().get('code'), 'permission_denied')
        self.cfop.refresh_from_db()

    def test_anonymous_full_request_redirects_to_login_instead_of_403(self):
        response = self.client.get(reverse('fiscal:cfop_list'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        self.assertIn('next=', response.url)

    def test_anonymous_ajax_request_returns_401_with_redirect_url(self):
        response = self.client.get(
            reverse('fiscal:cfop_list'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn('/accounts/login/', response.json()['redirect_url'])
