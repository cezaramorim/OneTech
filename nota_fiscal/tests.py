
# Create your tests here.

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
import json

from nota_fiscal.models import EmpresaAvancada

User = get_user_model()

class SalvarImportacaoViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Cria e autentica um usuário para passar pelo @login_required
        self.user = User.objects.create_user(username='tester', password='secret')
        self.client.force_login(self.user)

        self.url = reverse('nota_fiscal:salvar_importacao')  # ajuste se necessário

        # Campos mínimos em "nota" para não falhar validação
        self.common_payload = {
            "nota": {
                "numero_nota": "",
                "natureza_operacao": "",
                "data_emissao": "2025-01-01",
                "data_saida": "2025-01-01"
            },
            "produtos": [],
            "totais": {},
            "transporte": {},
            "duplicatas": [],
            "info_adicional": ""
        }

    def test_inferencia_cnpj_cria_empresa_pj(self):
        payload = {
            **self.common_payload,
            "fornecedor": {"cnpj": "12.345.678/0001-90", "razao_social":"X", "nome_fantasia":"X"},
            "chave_acesso": "PJKEY1234567890PJKEY1234567890PJKEY1234567890"
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),              # envia JSON de verdade
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        emp = EmpresaAvancada.objects.get(cnpj="12345678000190")
        self.assertEqual(emp.tipo_empresa, 'PJ')

    def test_inferencia_cpf_cria_empresa_pf(self):
        payload = {
            **self.common_payload,
            "fornecedor": {"cpf": "123.456.789-09", "razao_social":"Y", "nome_fantasia":"Y"},
            "chave_acesso": "PFKEY1234567890PFKEY1234567890PFKEY1234567890"
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        emp = EmpresaAvancada.objects.get(cnpj="12345678909")
        self.assertEqual(emp.tipo_empresa, 'PF')

    def test_falha_sem_identificador(self):
        payload = {
            **self.common_payload,
            "fornecedor": {},  # sem cnpj nem cpf
            "chave_acesso": "NOIDKEY123"
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Identificador (CNPJ/CPF)", response.json().get("erro", ""))
