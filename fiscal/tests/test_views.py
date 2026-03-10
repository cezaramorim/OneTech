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

from fiscal.models import Cfop


class FiscalImportViewSmokeTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='smoke', password='smoke123')
        content_type = ContentType.objects.get_for_model(Cfop)
        self.user.user_permissions.add(Permission.objects.get(codename='add_cfop', content_type=content_type))
        self.client.login(username='smoke', password='smoke123')
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

    def create_excel_file(self):
        df = pd.DataFrame({
            'codigo': ['1101'],
            'descricao': ['Compra para industrializacao'],
            'categoria': ['Entrada'],
        })
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='CFOPs')
        output.seek(0)
        output.name = 'smoke.xlsx'
        return output

    def test_import_page_accepts_excel_upload(self):
        response = self.client.post(reverse('fiscal:import_fiscal_data'), {
            'excel_file': self.create_excel_file(),
            'import_type': 'cfop',
        })

        self.assertEqual(response.status_code, 302)
