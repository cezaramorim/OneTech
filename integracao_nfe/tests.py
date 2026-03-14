import hashlib
import hmac
import json
import time

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from control.models import Emitente
from nota_fiscal.models import NotaFiscal


class WebhookSecurityTests(TestCase):
    @override_settings(NFE_WEBHOOK_SECRET='segredo-teste', NFE_WEBHOOK_TOLERANCE_SECONDS=300)
    def test_webhook_sem_headers_retorna_401(self):
        response = self.client.post(
            reverse('integracao_nfe:webhook_sefaz'),
            data=json.dumps({'chave_acesso': 'x', 'status': 'AUTORIZADA'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)

    @override_settings(NFE_WEBHOOK_SECRET='segredo-teste', NFE_WEBHOOK_TOLERANCE_SECONDS=300)
    def test_webhook_assinatura_invalida_retorna_401(self):
        payload = json.dumps({'chave_acesso': 'x', 'status': 'AUTORIZADA'})
        timestamp = str(int(time.time()))
        assinatura_invalida = hmac.new(
            key=b'segredo-errado',
            msg=f'{timestamp}.'.encode('utf-8') + payload.encode('utf-8'),
            digestmod=hashlib.sha256,
        ).hexdigest()

        response = self.client.post(
            reverse('integracao_nfe:webhook_sefaz'),
            data=payload,
            content_type='application/json',
            HTTP_X_ONETECH_TIMESTAMP=timestamp,
            HTTP_X_ONETECH_SIGNATURE=assinatura_invalida,
        )
        self.assertEqual(response.status_code, 401)


class WebhookLifecycleTests(TestCase):
    def _assinar(self, payload, secret='segredo-teste'):
        timestamp = str(int(time.time()))
        assinatura = hmac.new(
            key=secret.encode('utf-8'),
            msg=f'{timestamp}.'.encode('utf-8') + payload.encode('utf-8'),
            digestmod=hashlib.sha256,
        ).hexdigest()
        return timestamp, assinatura

    @override_settings(NFE_WEBHOOK_SECRET='segredo-teste', NFE_WEBHOOK_TOLERANCE_SECONDS=300)
    def test_webhook_autoriza_quando_transicao_valida(self):
        nota = NotaFiscal.objects.create(
            numero='101',
            chave_acesso='1' * 44,
            natureza_operacao='Venda',
            tipo_operacao='1',
            status_sefaz='enviada',
        )
        payload = json.dumps(
            {
                'chave_acesso': nota.chave_acesso,
                'status': 'AUTORIZADA',
                'protocolo': '135240000000001',
                'motivo': 'Autorizado o uso da NF-e',
            }
        )
        timestamp, assinatura = self._assinar(payload)

        response = self.client.post(
            reverse('integracao_nfe:webhook_sefaz'),
            data=payload,
            content_type='application/json',
            HTTP_X_ONETECH_TIMESTAMP=timestamp,
            HTTP_X_ONETECH_SIGNATURE=assinatura,
        )
        self.assertEqual(response.status_code, 200)
        nota.refresh_from_db()
        self.assertEqual(nota.status_sefaz, 'autorizada')
        self.assertEqual(nota.protocolo_autorizacao, '135240000000001')

    @override_settings(NFE_WEBHOOK_SECRET='segredo-teste', NFE_WEBHOOK_TOLERANCE_SECONDS=300)
    def test_webhook_retorna_409_quando_transicao_invalida(self):
        nota = NotaFiscal.objects.create(
            numero='102',
            chave_acesso='2' * 44,
            natureza_operacao='Venda',
            tipo_operacao='1',
            status_sefaz='cancelada',
        )
        payload = json.dumps({'chave_acesso': nota.chave_acesso, 'status': 'AUTORIZADA'})
        timestamp, assinatura = self._assinar(payload)

        response = self.client.post(
            reverse('integracao_nfe:webhook_sefaz'),
            data=payload,
            content_type='application/json',
            HTTP_X_ONETECH_TIMESTAMP=timestamp,
            HTTP_X_ONETECH_SIGNATURE=assinatura,
        )
        self.assertEqual(response.status_code, 409)


class EmissaoPreGateTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username='emissor',
            email='emissor@example.com',
            password='secret123'
        )
        self.client.force_login(self.user)
        self.emitente = Emitente.objects.create(
            razao_social='Emitente PreGate',
            cnpj='44444444000191',
            is_default=True,
        )

    def test_emitir_bloqueia_nota_invalida_no_pre_gate(self):
        nota = NotaFiscal.objects.create(
            numero='999',
            chave_acesso='9' * 44,
            natureza_operacao='Venda',
            tipo_operacao='1',
            emitente_proprio_id=self.emitente.pk,
            valor_total_nota='10.00',
            modelo_documento='55',
            ambiente='2',
        )
        response = self.client.post(
            reverse('integracao_nfe:emitir_nfe'),
            data=json.dumps({'nota_id': nota.pk}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get('success'))
        self.assertIn('errors', data)
        self.assertEqual(data.get('message'), 'Nota reprovada no gate de pre-emissao.')
        nota.refresh_from_db()
        self.assertIsNotNone(nota.pre_emissao_validada_em)
        self.assertEqual(nota.pre_emissao_ok, False)
        self.assertIsInstance(nota.pre_emissao_snapshot, dict)

    def test_emitir_sem_permissao_retorna_403(self):
        user_sem_permissao = get_user_model().objects.create_user(
            username='sem_perm_nfe',
            password='secret123',
        )
        self.client.force_login(user_sem_permissao)
        nota = NotaFiscal.objects.create(
            numero='1000',
            chave_acesso='8' * 44,
            natureza_operacao='Venda',
            tipo_operacao='1',
            emitente_proprio_id=self.emitente.pk,
            valor_total_nota='10.00',
            modelo_documento='55',
            ambiente='2',
        )
        response = self.client.post(
            reverse('integracao_nfe:emitir_nfe'),
            data=json.dumps({'nota_id': nota.pk}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)
