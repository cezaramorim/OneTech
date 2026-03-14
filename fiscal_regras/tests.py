import json
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from fiscal_regras.models import RegraAliquotaICMS
from fiscal_regras.services import get_resolver_metrics_snapshot, resolver_regra_icms_item


class FiscalRegrasSecurityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='user_fiscal_regras_sem_perm',
            password='secret123',
        )
        self.client.force_login(self.user)

    def test_lista_regras_sem_permissao_retorna_403(self):
        response = self.client.get(reverse('fiscal_regras:regra_icms_list'))
        self.assertEqual(response.status_code, 403)

    def test_resolver_api_sem_permissao_retorna_403(self):
        response = self.client.get(reverse('fiscal_regras:resolver_aliquota_icms_api'))
        self.assertEqual(response.status_code, 403)


class RegraAliquotaICMSConflitoTests(TestCase):
    def _build_base_regra(self, **overrides):
        data = {
            'ativo': True,
            'descricao': 'Regra Base',
            'ncm_prefixo': '1234',
            'tipo_operacao': '1',
            'modalidade': 'interna',
            'uf_origem': 'SP',
            'uf_destino': 'SP',
            'aliquota_icms': Decimal('18.00'),
            'fcp': Decimal('0.00'),
            'reducao_base_icms': Decimal('0.00'),
            'prioridade': 0,
            'vigencia_inicio': date(2026, 1, 1),
            'vigencia_fim': date(2026, 12, 31),
        }
        data.update(overrides)
        return RegraAliquotaICMS(**data)

    def test_bloqueia_conflito_de_vigencia_no_mesmo_escopo(self):
        self._build_base_regra(descricao='Regra 1').save()

        conflito = self._build_base_regra(
            descricao='Regra 2',
            vigencia_inicio=date(2026, 6, 1),
            vigencia_fim=date(2027, 6, 1),
        )

        with self.assertRaises(ValidationError):
            conflito.save()

    def test_permite_mesmo_escopo_sem_sobreposicao_de_vigencia(self):
        self._build_base_regra(descricao='Regra 2026').save()

        sem_conflito = self._build_base_regra(
            descricao='Regra 2027',
            vigencia_inicio=date(2027, 1, 1),
            vigencia_fim=date(2027, 12, 31),
        )
        sem_conflito.save()

        self.assertIsNotNone(sem_conflito.pk)

    def test_permite_sobreposicao_com_escopo_diferente(self):
        self._build_base_regra(descricao='Regra SP').save()

        diferente = self._build_base_regra(
            descricao='Regra RJ',
            uf_destino='RJ',
            vigencia_inicio=date(2026, 6, 1),
            vigencia_fim=date(2027, 6, 1),
        )
        diferente.save()

        self.assertIsNotNone(diferente.pk)


class ResolverRegraICMSServiceTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_prioriza_maior_especificidade_ncm(self):
        RegraAliquotaICMS.objects.create(
            ativo=True,
            descricao='Prefixo 12',
            ncm_prefixo='12',
            tipo_operacao='1',
            modalidade='interna',
            uf_origem='SP',
            uf_destino='SP',
            aliquota_icms=Decimal('10.00'),
            vigencia_inicio=date(2026, 1, 1),
        )
        RegraAliquotaICMS.objects.create(
            ativo=True,
            descricao='Prefixo 1234',
            ncm_prefixo='1234',
            tipo_operacao='1',
            modalidade='interna',
            uf_origem='SP',
            uf_destino='SP',
            aliquota_icms=Decimal('18.00'),
            vigencia_inicio=date(2026, 1, 1),
        )

        resolucao = resolver_regra_icms_item(
            data_emissao=date(2026, 3, 10),
            uf_emitente='SP',
            uf_destino='SP',
            ncm='12345678',
            tipo_operacao='1',
        )

        self.assertTrue(resolucao.found)
        self.assertEqual(resolucao.aliquota_icms, Decimal('18.00'))
        self.assertEqual(resolucao.origem, 'automatica')

    def test_prioriza_regra_vigente(self):
        RegraAliquotaICMS.objects.create(
            ativo=True,
            descricao='Regra 2025',
            ncm_prefixo='1234',
            tipo_operacao='1',
            modalidade='interna',
            uf_origem='SP',
            uf_destino='SP',
            aliquota_icms=Decimal('11.00'),
            vigencia_inicio=date(2025, 1, 1),
            vigencia_fim=date(2025, 12, 31),
        )
        RegraAliquotaICMS.objects.create(
            ativo=True,
            descricao='Regra 2026',
            ncm_prefixo='1234',
            tipo_operacao='1',
            modalidade='interna',
            uf_origem='SP',
            uf_destino='SP',
            aliquota_icms=Decimal('17.00'),
            vigencia_inicio=date(2026, 1, 1),
        )

        resolucao = resolver_regra_icms_item(
            data_emissao=date(2026, 2, 1),
            uf_emitente='SP',
            uf_destino='SP',
            ncm='12345678',
            tipo_operacao='1',
        )

        self.assertTrue(resolucao.found)
        self.assertEqual(resolucao.aliquota_icms, Decimal('17.00'))

    def test_fallback_manual_quando_sem_regra_e_sem_produto(self):
        resolucao = resolver_regra_icms_item(
            data_emissao=date(2026, 2, 1),
            uf_emitente='SP',
            uf_destino='SP',
            ncm='99999999',
            tipo_operacao='1',
        )

        self.assertFalse(resolucao.found)
        self.assertEqual(resolucao.origem, 'manual')
        self.assertEqual(resolucao.aliquota_icms, Decimal('0'))

    @override_settings(FISCAL_REGRAS_ENGINE_ENABLED=False, FISCAL_REGRAS_CACHE_TTL=0)
    def test_feature_flag_desliga_motor_e_forca_fallback(self):
        RegraAliquotaICMS.objects.create(
            ativo=True,
            descricao='Regra deveria ser ignorada',
            ncm_prefixo='1234',
            tipo_operacao='1',
            modalidade='interna',
            uf_origem='SP',
            uf_destino='SP',
            aliquota_icms=Decimal('18.00'),
            vigencia_inicio=date(2026, 1, 1),
        )

        resolucao = resolver_regra_icms_item(
            data_emissao=date(2026, 3, 10),
            uf_emitente='SP',
            uf_destino='SP',
            ncm='12345678',
            tipo_operacao='1',
        )

        self.assertFalse(resolucao.found)
        self.assertIn(resolucao.origem, ['manual', 'fallback_produto'])
        self.assertFalse(resolucao.contexto.get('engine_enabled'))

    @override_settings(FISCAL_REGRAS_ENGINE_ENABLED=True, FISCAL_REGRAS_CACHE_TTL=600)
    def test_cache_hit_incrementa_metricas(self):
        RegraAliquotaICMS.objects.create(
            ativo=True,
            descricao='Regra cache',
            ncm_prefixo='1234',
            tipo_operacao='1',
            modalidade='interna',
            uf_origem='SP',
            uf_destino='SP',
            aliquota_icms=Decimal('12.00'),
            vigencia_inicio=date(2026, 1, 1),
        )

        for _ in range(2):
            resolver_regra_icms_item(
                data_emissao=date(2026, 3, 10),
                uf_emitente='SP',
                uf_destino='SP',
                ncm='12345678',
                tipo_operacao='1',
            )

        metrics = get_resolver_metrics_snapshot()
        self.assertGreaterEqual(metrics.get('total', 0), 2)
        self.assertGreaterEqual(metrics.get('cache_hits', 0), 1)
        self.assertGreaterEqual(metrics.get('found', 0), 1)


class FiscalRegrasOperacaoViewsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username='super_fiscal_regras',
            email='super@example.com',
            password='secret123',
        )
        self.client.force_login(self.user)

    def test_importar_regras_json_cria_e_atualiza(self):
        payload = [
            {
                'ativo': True,
                'descricao': 'Regra Importada',
                'ncm_prefixo': '2203',
                'tipo_operacao': '1',
                'modalidade': 'interna',
                'uf_origem': 'SP',
                'uf_destino': 'SP',
                'aliquota_icms': '18.00',
                'fcp': '0.00',
                'reducao_base_icms': '0.00',
                'prioridade': 10,
                'vigencia_inicio': '2026-01-01',
                'vigencia_fim': '2026-12-31',
                'observacoes': 'import',
            }
        ]
        upload = SimpleUploadedFile(
            'regras.json',
            bytes(json.dumps(payload), encoding='utf-8'),
            content_type='application/json',
        )
        response = self.client.post(reverse('fiscal_regras:importar_regras'), {'arquivo': upload})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RegraAliquotaICMS.objects.count(), 1)

        payload[0]['descricao'] = 'Regra Importada Atualizada'
        upload_update = SimpleUploadedFile(
            'regras_update.json',
            bytes(json.dumps(payload), encoding='utf-8'),
            content_type='application/json',
        )
        response_update = self.client.post(reverse('fiscal_regras:importar_regras'), {'arquivo': upload_update})
        self.assertEqual(response_update.status_code, 200)
        self.assertEqual(RegraAliquotaICMS.objects.count(), 1)
        data_update = response_update.json()
        self.assertTrue(data_update.get('success'))
        self.assertIn('message', data_update)

    def test_validar_regras_retorna_conflitos(self):
        RegraAliquotaICMS.objects.create(
            ativo=True,
            descricao='Conflito A',
            ncm_prefixo='2203',
            tipo_operacao='1',
            modalidade='interna',
            uf_origem='SP',
            uf_destino='SP',
            aliquota_icms=Decimal('18.00'),
            vigencia_inicio=date(2026, 1, 1),
            vigencia_fim=date(2026, 3, 1),
        )
        RegraAliquotaICMS.objects.create(
            ativo=False,
            descricao='Conflito B',
            ncm_prefixo='2203',
            tipo_operacao='1',
            modalidade='interna',
            uf_origem='SP',
            uf_destino='SP',
            aliquota_icms=Decimal('17.00'),
            vigencia_inicio=date(2026, 1, 1),
            vigencia_fim=date(2026, 3, 1),
        )

        response = self.client.post(reverse('fiscal_regras:validar_regras'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('metrics', data)
        self.assertIn('conflitos', data)
        self.assertGreaterEqual(len(data.get('conflitos') or []), 1)
