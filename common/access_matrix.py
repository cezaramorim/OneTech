"""
Matriz central de acesso (Fase 2 baseline).
Gerada a partir do menu + endpoints criticos fora do menu.
"""

ROUTE_PERMISSION_MATRIX = {
    'accounts:cadastrar_grupo': ('auth.add_group',),
    'accounts:criar_usuario': ('accounts.add_user',),
    'accounts:lista_grupos': ('auth.view_group',),
    'accounts:lista_usuarios': ('accounts.view_user',),
    'comercial:condicao_pagamento_list': ('comercial.view_condicaopagamento',),
    'control:central_migracoes': (),
    'control:central_seguranca': (),
    'control:lista_emitentes': ('control.view_emitente',),
    'control:tenant_create': ('control.add_tenant',),
    'control:tenant_list': ('control.view_tenant',),
    'control:tenant_user_list': ('accounts.view_user',),
    'empresas:cadastrar_empresa': ('empresas.add_empresa',),
    'empresas:lista_categorias': ('empresas.view_categoriaempresa',),
    'empresas:lista_empresas': ('empresas.view_empresa',),
    'fiscal:cfop_list': ('fiscal.view_cfop',),
    'fiscal:import_fiscal_data': ('fiscal.add_cfop',),
    'fiscal:natureza_operacao_list': ('fiscal.view_naturezaoperacao',),
    'fiscal_regras:regra_icms_list': ('fiscal_regras.view_regraaliquotaicms',),
    'nota_fiscal:criar_nfe_saida': ('nota_fiscal.add_notafiscal',),
    'nota_fiscal:emitir_nfe_list': ('integracao_nfe.can_emit_nfe',),
    'nota_fiscal:entradas_nota': ('nota_fiscal.view_notafiscal',),
    'nota_fiscal:importar_xml': ('nota_fiscal.add_notafiscal',),
    'nota_fiscal:lancar_nota_manual': ('nota_fiscal.add_notafiscal',),
    'painel:home': ('painel.view_dashboard',),
    'producao:arracoamento_diario': ('producao.view_arracoamentosugerido',),
    'producao:cadastrar_curva': ('producao.add_curva',),
    'producao:cadastrar_lote': ('producao.add_lote',),
    'producao:gerenciar_curvas': ('producao.view_curvacrescimento',),
    'producao:gerenciar_eventos': ('producao.add_eventomanejo',),
    'producao:gerenciar_tanques': ('producao.view_tanque',),
    'producao:importar_curva': ('producao.add_curva',),
    'producao:lista_curvas': ('producao.view_curva',),
    'producao:lista_eventos': ('producao.view_eventomanejo',),
    'producao:lista_fasesproducao': ('producao.view_faseproducao',),
    'producao:lista_linhasproducao': ('producao.view_linhaproducao',),
    'producao:lista_lotes': ('producao.view_lote',),
    'producao:lista_malhas': ('producao.view_malha',),
    'producao:lista_statustanque': ('producao.view_statustanque',),
    'producao:lista_tanques': ('producao.view_tanque',),
    'producao:lista_tiposevento': ('producao.view_tipoevento',),
    'producao:lista_tipostanque': ('producao.view_tipotanque',),
    'producao:lista_tipotelas': ('producao.view_tipotela',),
    'producao:lista_unidades': ('producao.view_unidade',),
    'producao:povoamento_lotes': ('producao.add_lote',),
    'producao:reprocessar_lotes': ('producao.view_reprocessar_lotes',),
    'produto:cadastrar_produto': ('produto.add_produto',),
    'produto:lista_categorias': ('produto.view_categoriaproduto',),
    'produto:lista_produtos': ('produto.view_produto',),
    'produto:lista_unidades': ('produto.view_unidademedida',),
    'produto:manutencao_ncm': ('produto.view_ncm',),
    'relatorios:impressao_relatorios': ('relatorios.view_notafiscalrelatorio',),
    'relatorios:notas_entradas': ('relatorios.view_notafiscalrelatorio',),
}

PATH_PERMISSION_MATRIX = {
    '/api/v1/nota-fiscal/itens/': ('nota_fiscal.view_itemnotafiscal',),
    '/api/v1/notas-entradas/': ('nota_fiscal.view_notafiscal',),
    '/empresas/api/v1/fornecedores/': ('empresas.view_empresa',),
    '/gerenciamento/ping/': ('__auth_only__',),
    '/integracao-nfe/webhook/sefaz/': ('__webhook_hmac__',),
    '/painel/': ('painel.view_dashboard',),
    '/producao/api/ambiente/': ('producao.view_parametroambientaldiario',),
    '/producao/api/ambiente/upsert/': ('producao.change_parametroambientaldiario',),
    '/producao/api/arracoamento/aprovar/': (
        'producao.change_arracoamentosugerido',
        'producao.add_arracoamentorealizado',
    ),
    '/producao/api/arracoamento/sugestoes/': ('producao.view_lote',),
    '/producao/api/linhas-producao/': ('producao.view_linhaproducao',),
    '/produtos/api/racoes/': ('__auth_only__',),
    '/produtos/buscar-ncm/': ('__auth_only__',),
    '/produtos/ncm-autocomplete-produto/': ('__auth_only__',),
}


def permissions_for_route_name(route_name: str):
    return ROUTE_PERMISSION_MATRIX.get(route_name, tuple())


def permissions_for_path(path: str):
    return PATH_PERMISSION_MATRIX.get(path, tuple())
