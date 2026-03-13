import hashlib
import hmac
import json
import time

from django.test import TestCase, override_settings
from django.urls import reverse


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
