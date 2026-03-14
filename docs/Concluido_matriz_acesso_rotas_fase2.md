# Matriz de Acesso de Rotas (Fase 2 - baseline)

- Data de criacao: 2026-03-13
- Origem: menu dinamico + endpoints criticos fora do menu

## Rotas do menu

| Menu | Rota (url_name) | Permissao(s) | Fonte |
|---|---|---|---|
| Admin > Listar Clientes | `control:tenant_list` | `control.view_tenant` | menu |
| Admin > Novo Cliente | `control:tenant_create` | `control.add_tenant` | menu |
| Admin > Usuários por Cliente | `control:tenant_user_list` | `accounts.view_user` | menu |
| Admin > Central de Migracoes | `control:central_migracoes` | `-` | menu |
| Configurações > Emitentes / Filiais | `control:lista_emitentes` | `control.view_emitente` | menu |
| Configurações > Novo Usuário | `accounts:criar_usuario` | `accounts.add_user` | menu |
| Configurações > Lista de Usuários | `accounts:lista_usuarios` | `accounts.view_user` | menu |
| Configurações > Novo Grupo | `accounts:cadastrar_grupo` | `auth.add_group` | menu |
| Configurações > Lista de Grupos | `accounts:lista_grupos` | `auth.view_group` | menu |
| Lotes > Reprocessar Lotes | `producao:reprocessar_lotes` | `producao.view_reprocessar_lotes` | menu |
| Empresas > Cadastrar Empresa | `empresas:cadastrar_empresa` | `empresas.add_empresa` | menu |
| Empresas > Lista de Empresas | `empresas:lista_empresas` | `empresas.view_empresa` | menu |
| Empresas > Categorias | `empresas:lista_categorias` | `empresas.view_categoriaempresa` | menu |
| Produtos > Cadastro Produtos | `produto:cadastrar_produto` | `produto.add_produto` | menu |
| Produtos > Listar Produtos | `produto:lista_produtos` | `produto.view_produto` | menu |
| Produtos > Categorias de Produto | `produto:lista_categorias` | `produto.view_categoriaproduto` | menu |
| Produtos > Unidades de Medida | `produto:lista_unidades` | `produto.view_unidademedida` | menu |
| Produtos > NCM | `produto:manutencao_ncm` | `produto.view_ncm` | menu |
| Produção > Gerenciar Tanques | `producao:gerenciar_tanques` | `producao.view_tanque` | menu |
| Produção > Lista de Tanques | `producao:lista_tanques` | `producao.view_tanque` | menu |
| Produção > Importar Curva | `producao:importar_curva` | `producao.add_curva` | menu |
| Produção > Cadastrar Curva | `producao:cadastrar_curva` | `producao.add_curva` | menu |
| Produção > Lista de Curvas | `producao:lista_curvas` | `producao.view_curva` | menu |
| Produção > Gerenciar Curvas | `producao:gerenciar_curvas` | `producao.view_curvacrescimento` | menu |
| Produção > Cadastrar Lote | `producao:cadastrar_lote` | `producao.add_lote` | menu |
| Produção > Lista de Lotes | `producao:lista_lotes` | `producao.view_lote` | menu |
| Produção > Povoamento de Lotes | `producao:povoamento_lotes` | `producao.add_lote` | menu |
| Produção > Arraçoamento Diário | `producao:arracoamento_diario` | `producao.view_arracoamentosugerido` | menu |
| Produção > Gerenciar Eventos | `producao:gerenciar_eventos` | `producao.add_eventomanejo` | menu |
| Produção > Lista de Eventos | `producao:lista_eventos` | `producao.view_eventomanejo` | menu |
| Produção > Unidades | `producao:lista_unidades` | `producao.view_unidade` | menu |
| Produção > Malhas | `producao:lista_malhas` | `producao.view_malha` | menu |
| Produção > Tipos de Tela | `producao:lista_tipotelas` | `producao.view_tipotela` | menu |
| Produção > Linhas de Produção | `producao:lista_linhasproducao` | `producao.view_linhaproducao` | menu |
| Produção > Fases de Produção | `producao:lista_fasesproducao` | `producao.view_faseproducao` | menu |
| Produção > Status de Tanque | `producao:lista_statustanque` | `producao.view_statustanque` | menu |
| Produção > Tipos de Tanque | `producao:lista_tipostanque` | `producao.view_tipotanque` | menu |
| Produção > Tipos de Evento | `producao:lista_tiposevento` | `producao.view_tipoevento` | menu |
| Comercial > Condicao de Pagamento | `comercial:condicao_pagamento_list` | `comercial.view_condicaopagamento` | menu |
| Nota Fiscal > Criar NF-e (Saída) | `nota_fiscal:criar_nfe_saida` | `nota_fiscal.add_notafiscal` | menu |
| Nota Fiscal > Importar XML (Entrada) | `nota_fiscal:importar_xml` | `nota_fiscal.add_notafiscal` | menu |
| Nota Fiscal > Lançar Nota Manual (Entrada) | `nota_fiscal:lancar_nota_manual` | `nota_fiscal.add_notafiscal` | menu |
| Nota Fiscal > Emitir NF-e | `nota_fiscal:emitir_nfe_list` | `integracao_nfe.can_emit_nfe` | menu |
| Nota Fiscal > Entradas de Nota | `nota_fiscal:entradas_nota` | `nota_fiscal.view_notafiscal` | menu |
| Fiscal > CFOPs | `fiscal:cfop_list` | `fiscal.view_cfop` | menu |
| Fiscal > Naturezas de Operação | `fiscal:natureza_operacao_list` | `fiscal.view_naturezaoperacao` | menu |
| Fiscal > Classificacao Fiscal | `produto:manutencao_ncm` | `produto.view_ncm` | menu |
| Fiscal > Importar Dados Fiscais | `fiscal:import_fiscal_data` | `fiscal.add_cfop` | menu |
| Fiscal > Regras ICMS (NCM) | `fiscal_regras:regra_icms_list` | `fiscal_regras.view_regraaliquotaicms` | menu |
| Relatórios > Notas de Entrada | `relatorios:notas_entradas` | `relatorios.view_notafiscalrelatorio` | menu |
| Relatórios > Impressão de Relatórios | `relatorios:impressao_relatorios` | `relatorios.view_notafiscalrelatorio` | menu |

## Endpoints criticos fora do menu

| Recurso | Rota/Path | Regra de acesso |
|---|---|---|
| control:ping | `/gerenciamento/ping/` | AUTH only (login_required) |
| integracao_nfe:webhook_sefaz | `/integracao-nfe/webhook/sefaz/` | HMAC+timestamp (401 se invalido) |
| common_api:notas_entradas | `/api/v1/notas-entradas/` | DRF view_* permission |
| common_api:itens_nota | `/api/v1/nota-fiscal/itens/` | DRF view_* permission |
| common_api:fornecedores | `/empresas/api/v1/fornecedores/` | DRF view_* permission |
