import json
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from control.models import Emitente
from empresas.models import Empresa
from nota_fiscal.models import DuplicataNotaFiscal, ItemNotaFiscal, NotaFiscal
from nota_fiscal.services.pre_emissao import validar_nota_pre_emissao
from produto.models import Produto


User = get_user_model()


class ImportacaoXmlNotaFiscalTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='nf_super',
            email='nf_super@example.com',
            password='secret123',
        )
        self.user = User.objects.create_user(
            username='nf_user',
            password='secret123',
        )
        self.url_importar_xml = reverse('nota_fiscal:api_importar_xml_nfe')
        self.url_processar_xml = reverse('nota_fiscal:api_processar_importacao_xml')

    def test_importar_xml_sem_permissao_retorna_403(self):
        self.client.force_login(self.user)
        xml_file = SimpleUploadedFile(
            'nota.xml',
            b'<xml></xml>',
            content_type='application/xml',
        )
        response = self.client.post(self.url_importar_xml, {'xml': xml_file})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json().get('success'))

    def test_importar_xml_invalido_retorna_400(self):
        self.client.force_login(self.superuser)
        txt_file = SimpleUploadedFile(
            'nota.txt',
            b'nao e xml',
            content_type='text/plain',
        )
        response = self.client.post(self.url_importar_xml, {'xml': txt_file})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json().get('success'))


class ContratoDominioNotaFiscalTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='nf_domain_super',
            email='nf_domain_super@example.com',
            password='secret123',
        )
        self.client.force_login(self.superuser)
        self.url_importar_xml = reverse('nota_fiscal:api_importar_xml_nfe')
        self.url_processar_xml = reverse('nota_fiscal:api_processar_importacao_xml')

        self.emitente = Emitente.objects.create(
            razao_social='Emitente Teste',
            cnpj='11111111000191',
            is_default=True,
            uf='SP',
        )
        self.destinatario = Empresa.objects.create(
            tipo_empresa='pj',
            razao_social='Cliente Teste',
            cnpj='22222222000191',
            uf='SP',
            cliente=True,
            status_empresa='ativa',
        )
        self.fornecedor = Empresa.objects.create(
            tipo_empresa='pj',
            razao_social='Fornecedor Teste',
            cnpj='33333333000191',
            uf='SP',
            fornecedor=True,
            status_empresa='ativa',
        )

    def test_editar_saida_renderiza_formulario_de_saida(self):
        nota = NotaFiscal.objects.create(
            numero='1001',
            chave_acesso='S' * 44,
            natureza_operacao='Venda',
            tipo_operacao='1',
            emitente_proprio_id=self.emitente.pk,
            destinatario=self.destinatario,
        )
        response = self.client.get(reverse('nota_fiscal:editar_nota', kwargs={'pk': nota.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="emitente_proprio"')

    def test_editar_entrada_renderiza_formulario_de_entrada(self):
        nota = NotaFiscal.objects.create(
            numero='2001',
            chave_acesso='E' * 44,
            natureza_operacao='Compra',
            tipo_operacao='0',
            emitente=self.fornecedor,
            destinatario=self.destinatario,
        )
        response = self.client.get(reverse('nota_fiscal:editar_nota', kwargs={'pk': nota.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="emitente"')

    def test_criar_saida_aplica_defaults_de_cabecalho(self):
        response = self.client.post(
            reverse('nota_fiscal:criar_nfe_saida'),
            data={
                'emitente_proprio': str(self.emitente.pk),
                'destinatario': str(self.destinatario.pk),
                'natureza_operacao': 'Venda de mercadoria',
                'tipo_operacao': '1',
                'finalidade_emissao': '1',
                'quantidade_parcelas': '1',
                'data_emissao': '2026-03-14',
                'data_saida': '2026-03-14',
                'informacoes_adicionais': '',
                'condicao_pagamento': '',
                'condicao_pagamento_cadastro': '',
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get('success'))

        nota = NotaFiscal.objects.order_by('-id').first()
        self.assertIsNotNone(nota)
        self.assertEqual(nota.tipo_operacao, '1')
        self.assertEqual(nota.modelo_documento, '55')
        self.assertIn(nota.ambiente, ['1', '2'])

    def test_importar_xml_valido_retorna_preview(self):
        self.client.force_login(self.superuser)
        xml_content = b"""<?xml version='1.0' encoding='UTF-8'?>
<nfeProc>
  <NFe>
    <infNFe Id='NFe35100000000000000000550010000000011000000010'>
      <ide>
        <nNF>11</nNF>
        <dhEmi>2026-03-14T10:00:00-03:00</dhEmi>
      </ide>
      <emit>
        <xNome>Empresa Emitente Teste</xNome>
        <CNPJ>12345678000190</CNPJ>
      </emit>
      <dest>
        <xNome>Cliente Teste</xNome>
        <CPF>12345678909</CPF>
      </dest>
      <total>
        <ICMSTot>
          <vNF>10.00</vNF>
        </ICMSTot>
      </total>
      <det nItem='1'>
        <prod>
          <cProd>ABC1</cProd>
          <xProd>Produto Teste</xProd>
          <NCM>01012100</NCM>
        </prod>
      </det>
    </infNFe>
  </NFe>
</nfeProc>
"""
        xml_file = SimpleUploadedFile(
            'nota.xml',
            xml_content,
            content_type='application/xml',
        )
        response = self.client.post(self.url_importar_xml, {'xml': xml_file})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get('success'))
        self.assertIn('raw_payload', payload)
        self.assertIn('chave_acesso', payload)

    def test_processar_importacao_xml_sem_payload_essencial_retorna_400(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            self.url_processar_xml,
            data=json.dumps({'raw_payload': {}}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json().get('success'))

    def test_processar_importacao_xml_preenche_condicao_e_ncm_no_produto(self):
        self.client.force_login(self.superuser)
        payload = {
            'chave_acesso': '35100000000000000000550010000000011000000010',
            'force_update': True,
            'raw_payload': {
                'NFe': {
                    'infNFe': {
                        'ide': {
                            'nNF': '11',
                            'natOp': 'Compra para revenda',
                            'dhEmi': '2026-03-10T10:00:00-03:00',
                            'dSaiEnt': '2026-03-10',
                            'mod': '55',
                            'tpAmb': '2',
                        },
                        'emit': {
                            'xNome': 'Fornecedor XML',
                            'CNPJ': '12345678000190',
                            'IE': '123',
                            'enderEmit': {'xLgr': 'Rua A', 'nro': '10', 'xBairro': 'Centro', 'xMun': 'Sao Paulo', 'UF': 'SP', 'CEP': '01001000'},
                        },
                        'dest': {
                            'xNome': 'Destinatario XML',
                            'CNPJ': '98765432000199',
                            'enderDest': {'xLgr': 'Rua B', 'nro': '20', 'xBairro': 'Centro', 'xMun': 'Sao Paulo', 'UF': 'SP', 'CEP': '01002000'},
                        },
                        'total': {
                            'ICMSTot': {'vNF': '100.00', 'vProd': '100.00', 'vICMS': '0.00', 'vPIS': '0.00', 'vCOFINS': '0.00', 'vDesc': '0.00'}
                        },
                        'det': [
                            {
                                '@nItem': '1',
                                'prod': {'cProd': 'XML001', 'xProd': 'Produto XML', 'NCM': '2309.90.10', 'CFOP': '1102', 'uCom': 'UN', 'qCom': '1', 'vUnCom': '100.00', 'vProd': '100.00', 'vDesc': '0.00'},
                                'imposto': {
                                    'ICMS': {'ICMS00': {'orig': '0', 'vBC': '100.00', 'pICMS': '18.00', 'vICMS': '18.00'}},
                                    'IPI': {'IPITrib': {'pIPI': '5.00', 'vIPI': '5.00'}},
                                    'PIS': {'PISAliq': {'pPIS': '1.65', 'vPIS': '1.65'}},
                                    'COFINS': {'COFINSAliq': {'pCOFINS': '7.60', 'vCOFINS': '7.60'}},
                                },
                            }
                        ],
                        'cobr': {
                            'dup': [
                                {'nDup': '001', 'dVenc': '2026-03-17', 'vDup': '50.00'},
                                {'nDup': '002', 'dVenc': '2026-03-24', 'vDup': '50.00'},
                            ]
                        },
                    }
                }
            },
            'itens_para_revisar': [],
        }

        response = self.client.post(
            self.url_processar_xml,
            data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)

        nota = NotaFiscal.objects.get(chave_acesso=payload['chave_acesso'])
        self.assertEqual(nota.natureza_operacao, 'Compra para revenda')
        self.assertEqual(nota.condicao_pagamento, '7/14 DDL')
        self.assertEqual(nota.quantidade_parcelas, 2)

        produto = Produto.objects.get(codigo_fornecedor='XML001')
        self.assertTrue(hasattr(produto, 'detalhes_fiscais'))
        self.assertEqual(produto.detalhes_fiscais.ncm.codigo, '23099010')
        self.assertEqual(produto.detalhes_fiscais.origem_mercadoria, '0')
        self.assertEqual(produto.detalhes_fiscais.cfop, '1102')
        self.assertEqual(produto.detalhes_fiscais.unidade_comercial, 'UN')
        self.assertEqual(produto.detalhes_fiscais.icms, Decimal('18.00'))
        self.assertEqual(produto.detalhes_fiscais.ipi, Decimal('5.00'))
        self.assertEqual(produto.detalhes_fiscais.pis, Decimal('1.65'))
        self.assertEqual(produto.detalhes_fiscais.cofins, Decimal('7.60'))


class PreEmissaoDuplicatasTests(TestCase):
    def setUp(self):
        self.emitente = Emitente.objects.create(
            razao_social='Emitente Gate',
            cnpj='55555555000191',
            is_default=True,
            uf='SP',
        )
        self.destinatario = Empresa.objects.create(
            tipo_empresa='pj',
            razao_social='Cliente Gate',
            cnpj='66666666000191',
            uf='SP',
            cliente=True,
            status_empresa='ativa',
        )

    def _criar_nota_base(self):
        nota = NotaFiscal.objects.create(
            numero='3001',
            chave_acesso='3' * 44,
            natureza_operacao='Venda',
            tipo_operacao='1',
            finalidade_emissao='1',
            modelo_documento='55',
            ambiente='2',
            data_emissao=date(2026, 3, 10),
            emitente_proprio_id=self.emitente.pk,
            destinatario=self.destinatario,
            condicao_pagamento='21/28/35 DDL',
            quantidade_parcelas=3,
            valor_total_nota=Decimal('300.00'),
            valor_total_desconto=Decimal('0.00'),
        )
        ItemNotaFiscal.objects.create(
            nota_fiscal=nota,
            codigo='P001',
            descricao='Produto Teste',
            ncm='01012100',
            cfop='5102',
            quantidade=Decimal('1.000000'),
            valor_unitario=Decimal('300.000000'),
            valor_total=Decimal('300.000000'),
        )
        return nota

    def test_pre_emissao_aprova_duplicatas_com_vencimento_correto(self):
        nota = self._criar_nota_base()
        DuplicataNotaFiscal.objects.create(nota_fiscal=nota, numero='001', valor=Decimal('100.00'), vencimento=date(2026, 3, 31))
        DuplicataNotaFiscal.objects.create(nota_fiscal=nota, numero='002', valor=Decimal('100.00'), vencimento=date(2026, 4, 7))
        DuplicataNotaFiscal.objects.create(nota_fiscal=nota, numero='003', valor=Decimal('100.00'), vencimento=date(2026, 4, 14))

        resultado = validar_nota_pre_emissao(nota)
        self.assertTrue(resultado.get('ok'))

    def test_pre_emissao_reprova_vencimento_e_qtd_duplicatas_incorretos(self):
        nota = self._criar_nota_base()
        DuplicataNotaFiscal.objects.create(nota_fiscal=nota, numero='001', valor=Decimal('150.00'), vencimento=date(2026, 3, 30))
        DuplicataNotaFiscal.objects.create(nota_fiscal=nota, numero='002', valor=Decimal('150.00'), vencimento=date(2026, 4, 7))

        resultado = validar_nota_pre_emissao(nota)
        self.assertFalse(resultado.get('ok'))
        campos = [erro.get('field') for erro in resultado.get('errors', [])]
        self.assertIn('duplicatas', campos)
        self.assertIn('duplicata_1.vencimento', campos)
