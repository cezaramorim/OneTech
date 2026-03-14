
- Status: Iniciado

## 1) Objetivo
Implementar preenchimento automatico de aliquotas fiscais (principalmente ICMS interno e interestadual) com base no NCM do item, contexto da operacao e UF origem/destino, com suporte multitenant, auditoria, performance e possibilidade de acoplar/desacoplar sem impacto no restante do projeto.

## 2) Diretrizes de Arquitetura
- Modulo independente: criar um app dedicado chamado `fiscal_regras`.
- Tudo agrupado: models, services, api, templates, css/js, management commands, testes e migrations dentro de uma unica pasta de app.
- Integracao por contrato: NF-e consulta apenas um service (`resolver_regra_icms_item`) e nao conhece detalhes internos do modulo.
- Multi-tenant: dados de regras por banco do tenant (via roteamento ja existente), sem misturar tenants.
- Auditoria: item da nota grava qual regra foi aplicada e por que.
- Escalabilidade: busca por prefixo NCM e indices para reduzir custo de consulta.

## 2.1) Regra obrigatoria de templates (padrao do projeto)
- Todos os templates novos do modulo devem seguir exatamente o padrao ja usado no projeto:
  - layout via `render_ajax_or_base`
  - uso de `templates/partials/...`
  - identificadores `data-page`/`data-tela` conforme telas atuais
  - classes de formulario e botoes no mesmo estilo (`form-control`, `form-select`, `ajax-form`, `ajax-link`)
  - compatibilidade com temas existentes, sem criar design paralelo
- Nao criar estrutura visual nova. Reaproveitar componentes, convencoes de HTML e comportamento AJAX ja adotados.
## 3) Estrutura de Pastas e Arquivos

### 3.1) Novos arquivos (modulo independente)
Criar pasta/app:
- `fiscal_regras/`

Arquivos do app:
- `fiscal_regras/__init__.py`
- `fiscal_regras/apps.py`
- `fiscal_regras/admin.py`
- `fiscal_regras/models.py`
- `fiscal_regras/forms.py`
- `fiscal_regras/views.py`
- `fiscal_regras/urls.py`
- `fiscal_regras/services.py`
- `fiscal_regras/selectors.py`
- `fiscal_regras/permissions.py`
- `fiscal_regras/constants.py`
- `fiscal_regras/validators.py`
- `fiscal_regras/signals.py` (opcional)
- `fiscal_regras/management/commands/importar_regras_icms.py`
- `fiscal_regras/management/commands/exportar_regras_icms.py`
- `fiscal_regras/management/commands/validar_regras_icms.py`
- `fiscal_regras/migrations/0001_initial.py`

Templates do modulo:
- `templates/partials/fiscal_regras/regra_icms_list.html`
- `templates/partials/fiscal_regras/regra_icms_form.html`
- `templates/partials/fiscal_regras/regra_icms_import_result.html`

Assets proprios do modulo:
- `static/css/fiscal_regras.css`
- `static/js/fiscal_regras.js`

Testes do modulo:
- `fiscal_regras/tests/test_models.py`
- `fiscal_regras/tests/test_services.py`
- `fiscal_regras/tests/test_views.py`
- `fiscal_regras/tests/test_integration_nf.py`

Documentacao operacional:
- `docs/fiscal_regras_operacao.md`
- `docs/fiscal_regras_dicionario_campos.md`

### 3.2) Arquivos existentes que serao alterados
- `config/settings.py`
  - incluir app `fiscal_regras` em `INSTALLED_APPS`.
  - incluir `fiscal_regras` em `TENANT_APPS`.
- `config/urls.py`
  - incluir `path("fiscal-regras/", include("fiscal_regras.urls"))`.
- `common/menu_config.py`
  - incluir submenu para gestao de regras (com permissao).
- `nota_fiscal/models.py`
  - adicionar campos de rastreabilidade de regra aplicada por item.
- `nota_fiscal/views.py`
  - integrar chamada ao service de resolucao no fluxo de emissao/edicao.
- `templates/partials/nota_fiscal/form_nfe_saida.html` (ou equivalente usado na emissao)
  - refletir preenchimento automatico e indicador de regra aplicada.
- `templates/partials/nota_fiscal/editar_nota.html`
  - idem para edicao.
- `static/js/scripts.js` e/ou JS especifico da nota
  - disparar recalculo de aliquotas ao selecionar produto/NCM/UF.

## 4) Modelo de Dados (fiscal_regras)

### 4.1) Tabela principal: RegraAliquotaICMS
Campos sugeridos:
- `id`
- `ativo` (bool)
- `descricao` (char)
- `ncm_prefixo` (char, tamanho 2-8)
- `prefixo_len` (smallint)
- `tipo_operacao` (entrada/saida)
- `modalidade` (interna/interestadual)
- `uf_origem` (char2, nullable)
- `uf_destino` (char2, nullable)
- `origem_mercadoria` (char1, nullable)
- `cst_icms` (FK fiscal.CST, nullable)
- `csosn_icms` (FK fiscal.CSOSN, nullable)
- `aliquota_icms` (decimal 5,2)
- `fcp` (decimal 5,2, default 0)
- `reducao_base_icms` (decimal 5,2, default 0)
- `prioridade` (int, default 0)
- `vigencia_inicio` (date)
- `vigencia_fim` (date, nullable)
- `observacoes` (text, nullable)
- `created_at`, `updated_at`
- `created_by`, `updated_by` (FK user, nullable)

Indices obrigatorios:
- `(ativo, vigencia_inicio, vigencia_fim)`
- `(ncm_prefixo, prefixo_len)`
- `(modalidade, uf_origem, uf_destino)`
- `(tipo_operacao, prioridade)`

Constraint recomendada:
- impedir duplicidade de regra com mesmo escopo principal (prefixo + modalidade + UF + vigencia + CST/CSOSN + origem), ou no minimo detectar conflito no validador.

### 4.2) Tabela de auditoria opcional: RegraAliquotaAplicacaoLog
- guarda decisao do motor em eventos criticos (emitir nota/recalculo manual).
- util para suporte e rastreabilidade.

## 5) Campos novos em ItemNotaFiscal (nota_fiscal/models.py)
Adicionar:
- `regra_icms_aplicada_id` (FK para fiscal_regras.RegraAliquotaICMS, null)
- `regra_icms_descricao` (char/text snapshot)
- `aliquota_icms_origem` (manual/automatica)
- `motor_versao` (char)
- `dados_contexto_regra` (JSON, opcional)

Objetivo:
- manter historico imutavel do que foi aplicado na emissao.

## 6) Service principal e logica de resolucao

Arquivo:
- `fiscal_regras/services.py`

Assinatura sugerida:
- `resolver_regra_icms_item(*, data_emissao, uf_emitente, uf_destino, ncm, tipo_operacao, origem_mercadoria=None, cst_icms=None, csosn_icms=None, regime_tributario=None)`

Etapas da resolucao:
1. Normalizar entradas (NCM sem pontuacao, UFs upper, datas).
2. Determinar modalidade:
   - se `uf_emitente == uf_destino`: interna
   - senao: interestadual
3. Gerar candidatos de prefixo NCM por especificidade: 8, 6, 4, 2.
4. Filtrar regras ativas e vigentes.
5. Aplicar score de prioridade:
   - maior especificidade NCM
   - match exato de UF
   - match de CST/CSOSN
   - match de origem mercadoria
   - prioridade numerica
6. Retornar objeto final contendo:
   - aliquota_icms
   - reducao_base_icms
   - fcp
   - regra_id e metadados.
7. Se nada encontrado:
   - retornar fallback controlado (ex: usar detalhes fiscais do produto) + flag `sem_regra=True`.

## 7) Integracao com Emissao de Nota (fluxo)

Pontos de entrada:
- selecao de produto no item
- mudanca de destinatario (UF)
- mudanca de tipo de operacao
- mudanca de origem da mercadoria

Fluxo esperado:
1. UI identifica mudanca de contexto.
2. Chama endpoint do modulo para simular/aplicar regra.
3. Preenche campos do item (aliquota_icms, reducao_base_icms, etc).
4. Marca no item: "origem=automatica" e referencia da regra aplicada.
5. Permitir override manual apenas com permissao especifica.

## 8) Endpoints/API do modulo

Arquivos:
- `fiscal_regras/views.py`
- `fiscal_regras/urls.py`

Endpoints:
- `GET /fiscal-regras/` (lista)
- `GET /fiscal-regras/nova/` e `POST /fiscal-regras/nova/`
- `GET /fiscal-regras/<id>/editar/` e `POST ...`
- `POST /fiscal-regras/importar/`
- `POST /fiscal-regras/validar/`
- `GET /fiscal-regras/api/resolver-icms/` (simulacao para UI)

Seguranca:
- permissoes granulares:
  - `fiscal_regras.view_regraaliquotaicms`
  - `fiscal_regras.add_regraaliquotaicms`
  - `fiscal_regras.change_regraaliquotaicms`
  - `fiscal_regras.delete_regraaliquotaicms`
  - `fiscal_regras.override_aliquota_item`

## 9) Telas impactadas e ajustes obrigatorios

### 9.1) Novas telas
- Lista de regras ICMS por NCM.
- Formulario de regra (com validacao de conflito e vigencia).
- Importacao/exportacao de regras.

### 9.2) Telas existentes
- Emissao de Nota Fiscal:
  - exibir origem da aliquota (automatica/manual)
  - exibir badge "Regra aplicada: <codigo/descricao>"
  - recalculo automatico ao trocar produto/destinatario/tipo operacao.
- Edicao de Nota Fiscal:
  - mesmo comportamento da emissao.
- Cadastro de Produto (apenas complementar):
  - manter aliquota do produto como fallback quando sem regra.

## 10) Regras de fallback (para evitar bloqueio operacional)
- Se nao houver regra por NCM/UF:
  1. usar detalhes fiscais do produto (`aliquota_icms_interna/interestadual`)
  2. registrar motivo de fallback
  3. alertar usuario de forma nao bloqueante
- Permitir emissao mesmo sem regra, conforme permissao e politica de negocio.

## 11) Migrações e Tenant

### 11.1) Ordem de execucao
1. `migrate` no banco default.
2. `migrate_tenants --all` (ou slugs especificos).

### 11.2) Confirmacoes obrigatorias
- `showmigrations fiscal_regras` no default e em tenants.
- para cada tenant, confirmar registro em `django_migrations`.

### 11.3) Rollback planejado
- manter migration reversivel.
- feature flag para desativar preenchimento automatico sem remover modulo.

## 12) Performance
- Cache em memoria curta (ex: 60s) para regras mais usadas por chave:
  - `(tenant, uf_origem, uf_destino, ncm_prefixo, data, tipo_operacao, origem)`.
- Indices compostos conforme secao 4.
- Evitar N+1 com `select_related` para CST/CSOSN.

## 13) Testes obrigatorios

### 13.1) Unitarios
- prioridade por especificidade de NCM
- desempate por UF e prioridade
- vigencia
- fallback

### 13.2) Integracao
- emissao com UF igual (interna)
- emissao com UF diferente (interestadual)
- troca de destinatario recalcula item
- persistencia de regra aplicada no item

### 13.3) Regressao
- nao quebrar fluxo atual de produto/NCM/CFOP
- nao quebrar tenants sem regras carregadas

## 14) Usabilidade
- Selects com busca (select2) em NCM prefixo e filtros UF.
- visual claro de "automatica" vs "manual".
- botao "recalcular aliquota" por item e no lote.
- mensagens de validacao objetivas.

## 15) Plano de Implementacao (fases)

Fase 1 - Base do modulo
- criar app `fiscal_regras`
- model + admin + form + urls + views basicas
- migration inicial

Fase 2 - Motor de resolucao
- implementar `services.py` + `selectors.py`
- testes unitarios de ranking e vigencia

Fase 3 - Integracao com NF-e
- endpoint resolver
- integracao no JS da emissao/edicao
- salvar auditoria no `ItemNotaFiscal`

Fase 4 - Operacao
- import/export/validacao
- permissao de override
- documentacao operacional

Fase 5 - Hardening
- testes de regressao
- ajustes de performance
- checklist final de aceite

## 16) Checklist final de aceite
- [ ] Modulo isolado em pasta propria (`fiscal_regras`)
- [ ] Migrations aplicando no default e tenants
- [ ] UI de cadastro/edicao/lista de regras
- [ ] Resolucao automatica funcionando em emissao e edicao
- [ ] Fallback documentado e funcional
- [ ] Auditoria persistida por item
- [ ] Permissoes revisadas
- [ ] Testes unitarios e integracao verdes
- [ ] Documentacao operacional entregue

## 17) Observacao importante
Este plano foi desenhado para nao deixar regras espalhadas em varios apps sem controle. O modulo `fiscal_regras` centraliza dados, logica e interface administrativa, mantendo acoplamento minimo com `nota_fiscal` por meio de service/endpoint claro.


