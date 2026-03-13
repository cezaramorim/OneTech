import json

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from nota_fiscal.models import ItemNotaFiscal, NotaFiscal
from produto.models import NCM
from produto.ncm_services import inspect_ncm_duplicates, normalize_external_ncm_payload
from produto.ncm_utils import (
    carregar_metadados_ncm,
    formatar_codigo_ncm,
    normalizar_codigo_ncm,
    obter_nivel_ncm,
)
from produto.views import buscar_ncm_ajax


class NcmUtilsTests(TestCase):
    def test_normalizar_codigo_ncm_remove_pontuacao(self):
        self.assertEqual(normalizar_codigo_ncm('2309.90.10'), '23099010')

    def test_formatar_codigo_ncm_para_exibicao(self):
        self.assertEqual(formatar_codigo_ncm('23099010'), '2309.90.10')

    def test_obter_nivel_ncm_identifica_item_subitem(self):
        self.assertEqual(obter_nivel_ncm('2309.90.10'), 'Item/Subitem')
        self.assertEqual(obter_nivel_ncm('01.02'), 'Posi\u00e7\u00e3o')

    def test_carregar_metadados_ncm(self):
        meta = carregar_metadados_ncm()
        self.assertIn('vigencia', meta)
        self.assertIn('ato', meta)
        self.assertGreater(meta.get('total_itens', 0), 0)


class NcmServiceTests(TestCase):
    def test_normaliza_payload_externo_em_lista_pipe(self):
        payload = ['0102.21|Reprodutores de raca pura']
        normalized = normalize_external_ncm_payload(payload)

        self.assertEqual(normalized['Nomenclaturas'][0]['Codigo'], '0102.21')
        self.assertEqual(normalized['Nomenclaturas'][0]['Descricao'], 'Reprodutores de raca pura')

    def test_inspecao_de_duplicidade_identifica_grupo(self):
        keeper = NCM.objects.create(codigo='23099010', descricao='Descricao detalhada')
        duplicate = NCM.objects.create(codigo='99999999', descricao='NCM 23099010')
        NCM.objects.filter(pk=duplicate.pk).update(codigo='2309.90.10')

        summary = inspect_ncm_duplicates()

        self.assertEqual(summary['group_count'], 1)
        self.assertEqual(summary['groups'][0]['keeper_id'], keeper.pk)


class NcmModelTests(TestCase):
    def test_ncm_save_normaliza_codigo(self):
        ncm = NCM.objects.create(codigo='2309.90.10', descricao='Teste')
        self.assertEqual(ncm.codigo, '23099010')
        self.assertEqual(ncm.codigo_formatado, '2309.90.10')

    def test_item_nota_fiscal_save_normaliza_ncm(self):
        nota = NotaFiscal.objects.create(numero='1', natureza_operacao='Teste', chave_acesso='1' * 44)
        item = ItemNotaFiscal.objects.create(
            nota_fiscal=nota,
            codigo='ABC',
            descricao='Item',
            ncm='2309.90.10',
            quantidade=1,
            valor_unitario=1,
            valor_total=1,
        )
        self.assertEqual(item.ncm, '23099010')


class BuscarNcmAjaxTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.ncm = NCM.objects.create(codigo='2309.90.10', descricao='Preparacoes para alimentacao animal')
        self.ncm_hierarquico = NCM.objects.create(codigo='010221', descricao='Reprodutores de raca pura')
        NCM.objects.filter(pk=self.ncm_hierarquico.pk).update(codigo='0102.21')

    def test_busca_por_codigo_formatado_retorna_resultado_formatado(self):
        request = self.factory.get('/produto/buscar-ncm/', {'search': '2309.90.10'})
        request.user = type('User', (), {'is_authenticated': True})()
        response = buscar_ncm_ajax(request)

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertEqual(payload['results'][0]['id'], '23099010')
        self.assertEqual(payload['results'][0]['codigo_formatado'], '2309.90.10')

    def test_busca_por_descricao_retorna_resultado(self):
        request = self.factory.get('/produto/buscar-ncm/', {'search': 'alimentacao'})
        request.user = type('User', (), {'is_authenticated': True})()
        response = buscar_ncm_ajax(request)

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertTrue(any(item['id'] == '23099010' for item in payload['results']))

    def test_busca_sem_pontuacao_encontra_codigo_armazenado_com_ponto(self):
        request = self.factory.get('/produto/buscar-ncm/', {'search': '010221'})
        request.user = type('User', (), {'is_authenticated': True})()
        response = buscar_ncm_ajax(request)

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertTrue(any(item['codigo_formatado'] == '0102.21' for item in payload['results']))

    def test_busca_por_codigo_hierarquico_nao_traz_falso_positivo(self):
        NCM.objects.create(codigo='01012', descricao='- Cavalos:')
        NCM.objects.create(codigo='40101200', descricao='Reforcadas apenas com materias texteis')

        request = self.factory.get('/produto/buscar-ncm/', {'search': '01012'})
        request.user = type('User', (), {'is_authenticated': True})()
        response = buscar_ncm_ajax(request)

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        codigos = {item['id'] for item in payload['results']}
        self.assertIn('01012', codigos)
        self.assertNotIn('40101200', codigos)

class ProdutoSecurityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='user_produto_sem_perm',
            password='secret123',
        )
        self.client.force_login(self.user)

    def test_categoria_list_api_sem_permissao_retorna_403(self):
        response = self.client.get(reverse('produto:categoria-list-api'))
        self.assertEqual(response.status_code, 403)

    def test_produto_api_drf_sem_permissao_retorna_403(self):
        response = self.client.get('/produtos/api/v1/produtos/')
        self.assertEqual(response.status_code, 403)
