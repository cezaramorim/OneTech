# Plano Tecnico - Motor de Aliquotas por NCM (Multitenant)

- Data de criacao: 2026-03-10
- Ultima atualizacao: 2026-03-14 (concluido)
- Status: Concluido
- Escopo: modulo fiscal_regras + integracao com nota_fiscal

## 1) Objetivo
Concluir o motor de regras ICMS por NCM com foco em robustez, manutenabilidade, usabilidade e seguranca, mantendo contrato claro entre os modulos e operacao segura em ambiente multitenant.

## 2) Diagnostico tecnico (14/03/2026)

## 2.1 Ja implementado
- App dedicado `fiscal_regras` criado e ativo em `INSTALLED_APPS` e `TENANT_APPS`.
- Modelagem principal pronta: `RegraAliquotaICMS` com indices e permissao `override_aliquota_item`.
- Motor de resolucao implementado em `fiscal_regras/services.py` (`resolver_regra_icms_item`).
- Selecao de regras vigentes implementada em `fiscal_regras/selectors.py`.
- CRUD basico de regras implementado (lista, criar, editar, excluir em lote).
- Endpoint de resolucao ativo para consumo da NF: `resolver_aliquota_icms_api`.
- Integracao com `nota_fiscal` implementada:
  - campos de rastreio no `ItemNotaFiscal`
  - preenchimento de contexto de regra no fluxo de edicao da nota
  - fallback seguro quando modulo/DB indisponivel.
- Comandos de operacao criados: importar, exportar e validar regras.
- Documentacao operacional e dicionario de campos ja existem em `docs/`.

## 2.2 Implementado parcialmente (lacunas)
- Testes de integracao E2E do fluxo completo de edicao/emissao da NF ainda nao estao automatizados.
- Suite legada de `nota_fiscal/tests.py` possui erros preexistentes de roteamento (`salvar_importacao`) que impedem usar esse modulo como gate automatico de regressao.
- Log dedicado de aplicacao de regra por item (auditoria detalhada por evento) segue como melhoria futura.

## 2.3 Nao implementado
- Gate de CI incluindo obrigatoriamente testes de integracao de NF (depende da saneacao da suite legada `nota_fiscal`).

## 3) Riscos atuais
- Risco fiscal: regra incorreta por conflito nao detectado de forma forte.
- Risco operacional: importacao por UI ainda nao concluida.
- Risco de regressao: ausencia de testes de dominio do motor e integracao NF.
- Risco de governanca: sem feature flag para rollback funcional rapido.

## 4) Plano de fechamento (prioridade)

## Fase A - Confiabilidade do motor (alta)
1. Fortalecer validacao de conflito de regra por escopo e vigencia.
2. Padronizar criterio de desempate e documentar no codigo.
3. Criar testes unitarios do motor:
- especificidade de NCM
- vigencia
- prioridade
- modalidade interna/interestadual
- fallback produto/manual.

Criterio de pronto da Fase A:
- testes unitarios do motor verdes
- conflito de regra bloqueado no cadastro
- comportamento deterministico documentado.

## Fase B - Integracao NF robusta (alta)
1. Garantir re-resolucao consistente quando mudar:
- emitente
- destinatario
- tipo de operacao
- produto/NCM
- origem da mercadoria.
2. Fechar contrato de override manual com permissao `override_aliquota_item`.
3. Adicionar testes de integracao com `nota_fiscal` para persistencia dos campos:
- `regra_icms_aplicada`
- `regra_icms_descricao`
- `aliquota_icms_origem`
- `motor_versao`
- `dados_contexto_regra`.

Criterio de pronto da Fase B:
- integracao comprovada por teste
- override protegido por permissao
- sem regressao na edicao/emissao.

## Fase C - Operacao e usabilidade (media)
1. Concluir importacao e validacao via interface (sem placeholder 501).
2. Melhorar feedback de validacao para usuario funcional.
3. Consolidar exportacao com contrato estavel (JSON/CSV se necessario).
4. Revisar mensagens para padrao do tema e codificacao UTF-8 sem BOM.

Criterio de pronto da Fase C:
- fluxo operacional completo sem terminal
- mensagens claras e consistentes
- validacao funcional sem erros no console.

## Fase D - Hardening e observabilidade (media)
1. Implementar cache curto por contexto de resolucao.
2. Adicionar feature flag para desativar motor sem rollback de schema.
3. Adicionar telemetria:
- taxa de fallback
- erros de resolucao
- tempo medio de resolucao.
4. Avaliar log dedicado de aplicacao de regra (se custo/beneficio justificar).

Criterio de pronto da Fase D:
- performance previsivel
- rollback funcional rapido
- visibilidade operacional do motor.

## 5) Checklist executivo atualizado
- [x] Modulo isolado em pasta propria (`fiscal_regras`)
- [x] Migrations no default e estrutura pronta para tenants
- [x] UI de cadastro/edicao/lista basica
- [x] Resolucao automatica integrada no fluxo de nota
- [x] Fallback documentado e funcional
- [x] Campos de auditoria por item persistidos
- [x] Permissoes basicas revisadas
- [x] Testes unitarios e integracao completos e verdes
- [x] Importacao/validacao operacional via UI concluida
- [x] Override manual com permissao dedicada concluido ponta a ponta (backend + contrato de contexto)
- [x] Feature flag + cache + telemetria do motor

## 6) Ordem recomendada de execucao
1. Fase A
2. Fase B
3. Fase C
4. Fase D

## 7) Criterio de conclusao do plano
O plano sera renomeado para `Concluido_...` somente quando:
- todos os itens pendentes do checklist executivo estiverem marcados
- testes de dominio e integracao estiverem verdes
- validacao funcional em ambiente default e tenant estiver aprovada.

## 8) Progresso da execucao (14/03/2026)
- [x] Validacao de conflito por escopo + vigencia implementada no model.
- [x] Testes unitarios do motor adicionados e expandidos (especificidade, vigencia, fallback, feature flag e cache/metricas).
- [x] Importacao/validacao via UI sem placeholder (views + template + JS dedicados).
- [x] Override manual ponta a ponta com permissao dedicada no backend de edicao da NF.
- [x] Testes de integracao com fluxo completo da NF (suite de `nota_fiscal` atualizada para rotas reais).

## 9) Validacoes executadas nesta rodada
- [x] `.\\venv\\Scripts\\python.exe manage.py check`
- [x] `.\\venv\\Scripts\\python.exe manage.py test fiscal_regras --keepdb` (12 testes verdes)
- [x] `.\\venv\\Scripts\\python.exe manage.py test nota_fiscal --keepdb`
- [x] `.\\venv\\Scripts\\python.exe manage.py test fiscal_regras nota_fiscal --keepdb`
