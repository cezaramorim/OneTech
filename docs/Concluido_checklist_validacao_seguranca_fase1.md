# Checklist de Validacao - Seguranca Fase 1

- Data de criacao: 2026-03-13
- Ultima atualizacao: 2026-03-14
- Status: Concluido (validado por suite automatizada)
- Objetivo: validar em ambiente funcional os controles de autenticacao e permissao aplicados na Fase 1.

## Perfis de teste

Use 3 usuarios para validar:

1. `anonimo` (nao logado)
2. `usuario_sem_permissoes` (logado sem permissoes dos modulos testados)
3. `usuario_com_permissoes` (logado com permissoes do modulo em teste)

## Resultado esperado padrao

- Recurso protegido por `login_required`:
  - anonimo: `302` para `/accounts/login/`
- Recurso protegido por `permission_required`:
  - usuario_sem_permissoes: `403`
  - usuario_com_permissoes: `200` (ou `302` de fluxo legitimo de POST)
- API webhook assinada:
  - assinatura ausente/invalida: `401`

## Bloco 1 - Control

### 1.1 Ping
- URL: `/gerenciamento/ping/`
- Esperado:
  - anonimo: `302`
  - logado: `200`

## Bloco 2 - Produto

### 2.1 Categoria API auxiliar
- URL: `/produtos/api/categorias/`
- Permissao esperada: `produto.view_categoriaproduto`
- Esperado:
  - sem permissao: `403`
  - com permissao: `200` (JSON lista)

### 2.2 API DRF produtos
- URL: `/produtos/api/v1/produtos/`
- Permissao esperada: `produto.view_produto`
- Esperado:
  - sem permissao: `403`
  - com permissao: `200`

## Bloco 3 - Nota Fiscal

### 3.1 Emitir NF-e
- URL: `/nota-fiscal/emitir/`
- Permissao esperada: `integracao_nfe.can_emit_nfe`
- Esperado:
  - sem permissao: `403`
  - com permissao: `200`

### 3.2 Criar NF-e de saida
- URL: `/nota-fiscal/criar-saida/`
- Permissao esperada: `nota_fiscal.add_notafiscal`
- Esperado:
  - sem permissao: `403`
  - com permissao: `200`

### 3.3 Entradas de nota
- URL: `/nota-fiscal/entradas/`
- Permissao esperada: `nota_fiscal.view_notafiscal`
- Esperado:
  - sem permissao: `403`
  - com permissao: `200`

## Bloco 4 - APIs comuns (common/api)

### 4.1 Notas de entrada (DRF)
- URL: `/api/v1/notas-entradas/`
- Permissao esperada: `nota_fiscal.view_notafiscal`
- Esperado:
  - sem permissao: `403`
  - com permissao: `200`

### 4.2 Itens da nota (DRF)
- URL: `/api/v1/nota-fiscal/itens/`
- Permissao esperada: `nota_fiscal.view_itemnotafiscal`
- Esperado:
  - sem permissao: `403`
  - com permissao: `200`

### 4.3 Fornecedores (DRF empresas)
- URL: `/empresas/api/v1/fornecedores/`
- Permissao esperada: `empresas.view_empresa`
- Esperado:
  - sem permissao: `403`
  - com permissao: `200`

## Bloco 5 - Accounts

### 5.1 Lista de usuarios
- URL: `/accounts/usuarios/`
- Permissao esperada: `accounts.view_user`
- Esperado:
  - sem permissao: `403`
  - com permissao: `200`

### 5.2 Lista de grupos
- URL: `/accounts/grupos/`
- Permissao esperada: `auth.view_group`
- Esperado:
  - sem permissao: `403`
  - com permissao: `200`

## Bloco 6 - Empresas

### 6.1 Lista de empresas
- URL: `/empresas/`
- Permissao esperada: `empresas.view_empresa`
- Esperado:
  - sem permissao: `403`
  - com permissao: `200`

### 6.2 Lista de categorias
- URL: `/empresas/categorias/`
- Permissao esperada: `empresas.view_categoriaempresa`
- Esperado:
  - sem permissao: `403`
  - com permissao: `200`

## Bloco 7 - Relatorios

### 7.1 Notas de entrada (view)
- URL: `/relatorios/notas-entradas/`
- Permissao esperada: `relatorios.view_notafiscalrelatorio`
- Esperado:
  - sem permissao: `403`
  - com permissao: `200`

### 7.2 Notas de entrada (API)
- URL: `/relatorios/api/v1/notas-entradas/`
- Permissao esperada: `relatorios.view_notafiscalrelatorio`
- Esperado:
  - sem permissao: `403`
  - com permissao: `200`

## Bloco 8 - Fiscal Regras

### 8.1 Lista de regras
- URL: `/fiscal-regras/`
- Permissao esperada: `fiscal_regras.view_regraaliquotaicms`
- Esperado:
  - sem permissao: `403`
  - com permissao: `200`

### 8.2 Resolver aliquota (API)
- URL: `/fiscal-regras/api/resolver-icms/`
- Permissao esperada: `fiscal_regras.view_regraaliquotaicms`
- Esperado:
  - sem permissao: `403`
  - com permissao: `200`

## Bloco 9 - Producao (endpoints reforcados)

### 9.1 Ultimos eventos
- URL: `/producao/api/ultimos-eventos/` (conforme rota do modulo)
- Permissao esperada: `producao.view_eventomanejo`
- Esperado:
  - sem permissao: `403`
  - com permissao: `200`

### 9.2 Linhas de producao (API)
- URL: `/producao/api/linhas-producao/` (conforme rota do modulo)
- Permissao esperada: `producao.view_linhaproducao`
- Esperado:
  - sem permissao: `403`
  - com permissao: `200`

### 9.3 Fases com tanques (API)
- URL: `/producao/api/fases-com-tanques/` (conforme rota do modulo)
- Permissao esperada: `producao.view_faseproducao`
- Esperado:
  - sem permissao: `403`
  - com permissao: `200`

## Bloco 10 - Webhook NFe

### 10.1 Webhook sem assinatura
- URL: `/integracao-nfe/webhook/sefaz/`
- Metodo: `POST`
- Esperado: `401`

### 10.2 Webhook com assinatura invalida
- URL: `/integracao-nfe/webhook/sefaz/`
- Metodo: `POST`
- Esperado: `401`

## Evidencia recomendada

Para cada caso, registrar:

1. usuario usado
2. URL/metodo
3. status HTTP recebido
4. print da tela (quando HTML) ou payload de resposta (quando API)

## Criterio de encerramento da Fase 1

- Todos os cenarios de negacao (`302/403/401`) validados.
- Todos os cenarios de acesso legitimo (`200/302 de fluxo`) validados.
- Sem regressao funcional nas telas principais apos validacao.


## Evidencia de execucao (2026-03-14)
- Comando executado:
  - `.\venv\Scripts\python.exe manage.py test common.tests control.tests producao.tests integracao_nfe.tests.WebhookSecurityTests nota_fiscal.tests.ImportacaoXmlNotaFiscalTests --keepdb`
- Resultado:
  - `72 testes executados, 72 aprovados (OK)`
- Cobertura validada:
  - matriz de acesso/menu
  - baseline de seguranca
  - negacao de autorizacao (401/403/302)
  - webhook NFe com assinatura
  - endpoints operacionais de producao

## Encerramento
- Checklist de validacao da Fase 1 concluido no ambiente de desenvolvimento/homologacao.
- Validacao operacional de producao segue nos checklists especificos em `docs/futuro/`.
