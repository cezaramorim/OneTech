import json
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import Permission
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from control.models import Emitente
from empresas.models import Empresa
from nota_fiscal.models import DuplicataNotaFiscal, ItemNotaFiscal, NotaFiscal, TransporteNotaFiscal
from nota_fiscal.services.pre_emissao import validar_nota_pre_emissao
from nota_fiscal.views import _get_emitente_ativo_id
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
        self.assertEqual(produto.detalhes_fiscais.aliquota_icms_interna, Decimal('18.00'))
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


class NotaFiscalFluxoE2ETests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='nf_e2e_super',
            email='nf_e2e_super@example.com',
            password='secret123',
        )
        self.user_sem_override = User.objects.create_user(
            username='nf_e2e_user',
            email='nf_e2e_user@example.com',
            password='secret123',
        )
        self.user_com_override = User.objects.create_user(
            username='nf_e2e_override',
            email='nf_e2e_override@example.com',
            password='secret123',
        )

        self.user_sem_override.user_permissions.add(
            Permission.objects.get(codename='change_notafiscal')
        )
        self.user_com_override.user_permissions.add(
            Permission.objects.get(codename='change_notafiscal'),
            Permission.objects.get(codename='override_aliquota_item'),
        )

        self.emitente_padrao = Emitente.objects.create(
            razao_social='Emitente E2E Padrao',
            cnpj='77777777000191',
            is_default=True,
            uf='SP',
        )
        self.emitente_secundario = Emitente.objects.create(
            razao_social='Emitente E2E Secundario',
            cnpj='88888888000191',
            is_default=False,
            uf='SP',
        )
        self.destinatario = Empresa.objects.create(
            tipo_empresa='pj',
            razao_social='Cliente E2E',
            cnpj='99999999000191',
            uf='SP',
            cliente=True,
            status_empresa='ativa',
        )

    def _criar_nota_saida_com_relacoes(self, numero, emitente):
        nota = NotaFiscal.objects.create(
            numero=str(numero),
            chave_acesso=str(numero).zfill(44),
            natureza_operacao='Venda E2E',
            tipo_operacao='1',
            finalidade_emissao='1',
            modelo_documento='55',
            ambiente='2',
            data_emissao=date(2026, 3, 14),
            data_saida=date(2026, 3, 14),
            emitente_proprio_id=emitente.id,
            destinatario_id=self.destinatario.id,
            condicao_pagamento='A vista',
            quantidade_parcelas=1,
            valor_total_nota=Decimal('100.00'),
            valor_total_desconto=Decimal('0.00'),
        )
        item = ItemNotaFiscal.objects.create(
            nota_fiscal=nota,
            codigo='PRD001',
            descricao='Produto E2E',
            ncm='23099010',
            cfop='5102',
            unidade='UN',
            quantidade=Decimal('1.000000'),
            valor_unitario=Decimal('100.000000'),
            valor_total=Decimal('100.000000'),
            desconto=Decimal('0.000000'),
            aliquota_icms=Decimal('18.00'),
        )
        duplicata = DuplicataNotaFiscal.objects.create(
            nota_fiscal=nota,
            numero='001',
            valor=Decimal('100.00'),
            vencimento=date(2026, 3, 14),
        )
        transporte = TransporteNotaFiscal.objects.create(
            nota_fiscal=nota,
            modalidade_frete='0',
            transportadora_nome='Transportadora E2E',
            transportadora_cnpj='12345678000199',
            quantidade_volumes=1,
            especie_volumes='CAIXA',
            peso_liquido=Decimal('10.0000'),
            peso_bruto=Decimal('12.0000'),
        )
        return nota, item, duplicata, transporte

    def _payload_edicao(self, nota, item, duplicata, transporte, manual_override):
        payload = {
            'numero': nota.numero,
            'emitente_proprio': str(nota.emitente_proprio_id),
            'destinatario': str(nota.destinatario_id),
            'tipo_operacao': '1',
            'finalidade_emissao': '1',
            'data_emissao': '2026-03-14',
            'data_saida': '2026-03-14',
            'natureza_operacao': '',
            'condicao_pagamento': '',
            'quantidade_parcelas': '1',
            'valor_total_desconto': '0.00',
            'valor_total_nota': '100.00',
            'informacoes_adicionais': 'E2E-edicao',

            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '1',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            'items-0-id': str(item.id),
            'items-0-codigo': item.codigo,
            'items-0-descricao': item.descricao,
            'items-0-ncm': item.ncm,
            'items-0-cfop': item.cfop,
            'items-0-unidade': item.unidade,
            'items-0-quantidade': '1.000000',
            'items-0-valor_unitario': '100.000000',
            'items-0-valor_total': '100.000000',
            'items-0-desconto': '0.000000',
            'items-0-aliquota_icms': '18.00',
            'items-0-aliquota_ipi': '',
            'items-0-aliquota_pis': '',
            'items-0-aliquota_cofins': '',
            'items-0-regra_icms_aplicada': '',
            'items-0-regra_icms_descricao': '',
            'items-0-aliquota_icms_origem': 'manual' if manual_override else '',
            'items-0-motor_versao': '',
            'items-0-dados_contexto_regra': '{"manual_override": true}' if manual_override else '',
            'duplicatas-TOTAL_FORMS': '1',
            'duplicatas-INITIAL_FORMS': '1',
            'duplicatas-MIN_NUM_FORMS': '0',
            'duplicatas-MAX_NUM_FORMS': '1000',
            'duplicatas-0-id': str(duplicata.id),
            'duplicatas-0-numero': duplicata.numero,
            'duplicatas-0-vencimento': duplicata.vencimento.isoformat(),
            'duplicatas-0-valor': '100.00',

            'transporte-TOTAL_FORMS': '1',
            'transporte-INITIAL_FORMS': '1',
            'transporte-MIN_NUM_FORMS': '0',
            'transporte-MAX_NUM_FORMS': '1',
            'transporte-0-id': str(transporte.id),
            'transporte-0-modalidade_frete': transporte.modalidade_frete or '0',
            'transporte-0-transportadora': '',
            'transporte-0-transportadora_nome': transporte.transportadora_nome or '',
            'transporte-0-transportadora_cnpj': transporte.transportadora_cnpj or '',
            'transporte-0-placa_veiculo': '',
            'transporte-0-uf_veiculo': '',
            'transporte-0-rntc': '',
            'transporte-0-quantidade_volumes': str(transporte.quantidade_volumes or 0),
            'transporte-0-especie_volumes': transporte.especie_volumes or '',
            'transporte-0-peso_liquido': str(transporte.peso_liquido or 0),
            'transporte-0-peso_bruto': str(transporte.peso_bruto or 0),
        }
        return payload

    def test_e2e_listagem_busca_default_e_tenant(self):
        nota_ok, _, _, _ = self._criar_nota_saida_com_relacoes(4001, self.emitente_padrao)
        nota_outro, _, _, _ = self._criar_nota_saida_com_relacoes(5001, self.emitente_secundario)
        self.client.force_login(self.superuser)

        response_default = self.client.get(reverse('nota_fiscal:emitir_nfe_list'), {'busca': '4001'})
        self.assertEqual(response_default.status_code, 200)
        self.assertContains(response_default, nota_ok.numero)
        self.assertNotContains(response_default, nota_outro.numero)

    def test_e2e_resolucao_emitente_ativo_com_tenant(self):
        class DummyTenant:
            emitente_padrao_id = 123

        class DummyRequest:
            tenant = DummyTenant()

        self.assertEqual(_get_emitente_ativo_id(DummyRequest()), 123)

    def test_e2e_edicao_bloqueia_override_sem_permissao(self):
        nota, item, duplicata, transporte = self._criar_nota_saida_com_relacoes(6001, self.emitente_padrao)
        self.client.force_login(self.user_sem_override)
        response = self.client.post(
            reverse('nota_fiscal:editar_nota', kwargs={'pk': nota.pk}),
            data=self._payload_edicao(nota, item, duplicata, transporte, manual_override=True),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Permissao insuficiente para override manual de aliquota')

    def test_e2e_edicao_permite_override_com_permissao(self):
        nota, item, duplicata, transporte = self._criar_nota_saida_com_relacoes(7001, self.emitente_padrao)
        self.client.force_login(self.user_com_override)
        response = self.client.post(
            reverse('nota_fiscal:editar_nota', kwargs={'pk': nota.pk}),
            data=self._payload_edicao(nota, item, duplicata, transporte, manual_override=True),
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('nota_fiscal:emitir_nfe_list'), response.headers.get('Location', ''))

    def test_e2e_importacao_xml_preview_e_processamento(self):
        self.client.force_login(self.superuser)
        xml_content = b"""<?xml version='1.0' encoding='UTF-8'?>
<nfeProc>
  <NFe>
    <infNFe Id='NFe35100000000000000000550010000000012000000010'>
      <ide><nNF>12</nNF><dhEmi>2026-03-14T10:00:00-03:00</dhEmi></ide>
      <emit><xNome>Fornecedor E2E</xNome><CNPJ>12345678000190</CNPJ></emit>
      <dest><xNome>Cliente E2E XML</xNome><CPF>12345678909</CPF></dest>
      <total><ICMSTot><vNF>10.00</vNF></ICMSTot></total>
      <det nItem='1'>
        <prod><cProd>E2E001</cProd><xProd>Produto E2E XML</xProd><NCM>01012100</NCM></prod>
      </det>
    </infNFe>
  </NFe>
</nfeProc>
"""
        preview = self.client.post(
            reverse('nota_fiscal:api_importar_xml_nfe'),
            {'xml': SimpleUploadedFile('e2e.xml', xml_content, content_type='application/xml')}
        )
        self.assertEqual(preview.status_code, 200)
        payload = preview.json()
        self.assertTrue(payload.get('success'))
        self.assertTrue(payload.get('raw_payload'))

    def test_e2e_erro_amigavel_json_malformado(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse('nota_fiscal:excluir_nota_multiplo'),
            data='{"ids":[1,2]',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('JSON', response.json().get('message', ''))
