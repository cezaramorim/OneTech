from django.test import TestCase

from nota_fiscal.models import ItemNotaFiscal, NotaFiscal
from produto.models import NCM
from produto.ncm_utils import formatar_codigo_ncm, normalizar_codigo_ncm


class NcmUtilsTests(TestCase):
    def test_normalizar_codigo_ncm_remove_pontuacao(self):
        self.assertEqual(normalizar_codigo_ncm('2309.90.10'), '23099010')

    def test_formatar_codigo_ncm_para_exibicao(self):
        self.assertEqual(formatar_codigo_ncm('23099010'), '2309.90.10')


class NcmModelTests(TestCase):
    def test_ncm_save_normaliza_codigo(self):
        ncm = NCM.objects.create(codigo='2309.90.10', descricao='Teste')
        self.assertEqual(ncm.codigo, '23099010')
        self.assertEqual(ncm.codigo_formatado, '2309.90.10')

    def test_item_nota_fiscal_save_normaliza_ncm(self):
        nota = NotaFiscal.objects.create(numero='1', natureza_operacao='Teste', chave_acesso='1'*44)
        item = ItemNotaFiscal.objects.create(nota_fiscal=nota, codigo='ABC', descricao='Item', ncm='2309.90.10', quantidade=1, valor_unitario=1, valor_total=1)
        self.assertEqual(item.ncm, '23099010')
