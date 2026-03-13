# Plano de Seguranca e Permissoes de Rotas/APIs

- Data de criacao: 2026-03-11
- Ultima atualizacao: 2026-03-13
- Status: Fase 2 concluida e Fase 3 em consolidacao final (auditoria operacional ativa)

## Fase 2 - Progresso atual
1. [x] Matriz baseline de rotas e permissoes gerada em docs/matriz_acesso_rotas_fase2.md.
2. [x] Inconsistencia de menu corrigida (relatorios:impressao_relatorios com permissao explicita).
3. [x] Teste de consistencia de menu adicionado (common/tests.py).
4. [x] Migrar validacao para matriz central em codigo (common/access_matrix.py + common/tests.py).
5. [x] Comando de auditoria criado: python manage.py auditar_matriz_acesso.
6. [x] Revisao de prefixos/API documentada em docs/analise_prefixos_api_fase2.md (sem breaking change nesta fase).
7. [x] Padronizacao de 403 JSON para views AJAX com @login_required_json + permissao (permission_required_json).
8. [x] Contrato de erro 403 padronizado em APIs de relatorios (campo code=permission_denied).
9. [x] Handler global DRF configurado para padrao de resposta 401/403 com codigo estavel.
10. [x] 403 JSON manual padronizado em modulos fiscais e nota fiscal (empresas/fiscal/nota_fiscal/integracao_nfe).
11. [x] Testes de contrato adicionados/ajustados para retorno code em 403/401 (accounts/relatorios/empresas/fiscal).
12. [x] Varredura final de 403 JSON concluida: respostas de permissao negada padronizadas com code=permission_denied nos modulos mapeados.
13. [x] Auditoria automatica menu x matriz executavel e validada via comando manage.py auditar_matriz_acesso.
14. [x] Teste automatizado do comando de auditoria adicionado em common/tests.py.
15. [x] Hardening de sessao/transporte implementado em settings.py com controle por variaveis de ambiente (USE_HTTPS e flags SECURE_*).
16. [x] Testes de isolamento por host/tenant no middleware adicionados (resolucao por dominio ativo/inativo e bloqueio de admin em contexto tenant).
17. [x] Telemetria de autorizacao negada implementada (logger security.authz com trilha de usuario/rota/host/tenant em decorators e handler DRF).
18. [x] Comando de baseline de seguranca OWASP basico criado (manage.py validar_baseline_seguranca).
19. [x] Checklist operacional OWASP Fase 3 documentado (docs/checklist_owasp_basico_fase3.md).
20. [x] Modo estrito no baseline de seguranca implementado (validar_baseline_seguranca --strict) para gate de producao.
21. [x] Testes de contrato dos paths criticos da PATH_PERMISSION_MATRIX adicionados em common/tests.py (anon/autenticado sem permissao/ping/webhook).
22. [x] Comando unificado de auditoria de seguranca criado (manage.py auditar_seguranca).
23. [x] Politica do painel concluida com permissao dedicada (painel.view_dashboard) e cobertura de testes.
24. [x] Cobertura de seguranca do modulo producao ampliada (matriz PATH + testes negativos de APIs operacionais).
25. [x] Endpoints auxiliares de produto incluidos na matriz PATH (/produtos/api/racoes/, uscar-ncm) com testes de contrato auth-only.

## Cobertura Completa por Modulo (Inventario Inicial)
Legenda:
- `ROTAS`: rotas mapeadas no `urls.py`
- `AUTH`: exige autenticacao (`login_required`/`login_required_json`/`IsAuthenticated`)
- `PERM`: exige permissao granular (`permission_required`/`DjangoModelPermissions`)
- `GAP`: ponto critico identificado na revisao inicial

| Modulo | ROTAS | AUTH | PERM | GAP inicial |
|---|---|---|---|---|
| `accounts` | [x] | [x] | [x] | listas sensiveis alinhadas com permissao explicita (`accounts.*`/`auth.*`) |
| `comercial` | [x] | [x] | [x] | sem gap critico inicial |
| `control` | [x] | [x] | [x] | `ping_view` auth-only intencional para healthcheck interno (coberto por testes) |
| `empresas` | [x] | [x] | [x] | rotas de listagem/form/status alinhadas com permissao explicita |
| `fiscal` | [x] | [x] | [x] | sem gap critico inicial |
| `fiscal_regras` | [x] | [x] | [x] | sem gap critico inicial |
| `integracao_nfe` | [x] | [~] | [x] | `sefaz_webhook` protegido com HMAC + timestamp (anti-replay) |
| `nota_fiscal` | [x] | [x] | [x] | rotas criticas com permissao explicita (emissao/criacao/edicao/exclusao) |
| `painel` | [x] | [x] | [x] | permissao dedicada `painel.view_dashboard` aplicada e testada |
| `producao` | [x] | [x] | [x] | matriz PATH e testes de authz aplicados nas APIs operacionais criticas |
| `produto` | [x] | [x] | [x] | endpoints auxiliares mapeados na matriz PATH com contrato auth-only validado |
| `relatorios` | [x] | [x] | [x] | views/API protegidas com permissao de dominio (`relatorios.view_notafiscalrelatorio`) |
| `common/api` | [x] | [x] | [x] | `ProdutoViewSet`, `ItemNotaFiscalViewSet`, `NotaFiscalViewSet` e `FornecedorViewSet` com permissao granular (`view_*`) |

## Backlog Objetivo da Fase 1 (Critico)
1. [x] Proteger `integracao_nfe.views.sefaz_webhook` com assinatura HMAC + anti-replay.
2. [x] Definir politica e aplicar em `control.views.ping_view` (autenticacao obrigatoria).
3. [x] Fechar `produto.views.categoria_list_api` com auth + permissao.
4. [x] Aplicar permissao granular nos ViewSets sem `DjangoModelPermissions`:
- `common.api.produto.ProdutoViewSet`
- `common.api.item_nota_fiscal.ItemNotaFiscalViewSet`
- revisar `common.api.nota_fiscal.NotaFiscalViewSet` para permissao de dominio.
5. [x] Regularizar permissao explicita para emissao/criacao em `nota_fiscal.views` (rotas criticas).
6. [x] Adicionar testes negativos 401/403 para os gaps criticos fechados na Fase 1.
## Objetivo
Fortalecer seguranca de acesso no projeto com regras consistentes entre:
- visibilidade de menu
- autorizacao de rotas HTML
- autorizacao de APIs JSON/DRF
- contexto multi-tenant por dominio

Escopo principal:
- impedir acesso indevido por URL direta
- impedir acesso indevido por endpoint API direto no navegador/fetch
- reduzir superficie de ataque (webhooks, endpoints publicos e hardening de sessao)
- manter compatibilidade com o fluxo AJAX atual e com o plano de unificacao das listas

## Principios Tecnicos
- autorizacao no backend sempre prevalece sobre menu
- menu e backend devem compartilhar a mesma matriz de permissao
- defesa em profundidade: autenticacao + permissao + validacao de escopo
- alteracoes pequenas e rastreaveis por lote
- sem regressao de UX (mensagens, redirects e AJAX)
- sem scripts inline novos

## Diagnostico Consolidado (Base Atual)
1. Menu dinamico filtra por permissao corretamente no frontend (`common/context_processors.py`), porem parte das views nao replica permissao fina.
2. Existem views de listagem sensiveis com `login_required`/`login_required_json` sem `permission_required`.
3. Existem endpoints com exposicao desnecessaria ou sem autenticacao especifica.
4. Webhook de integracao esta sem validacao de autenticidade da origem.
5. Configuracoes de hardening de cookies/transporte nao estao explicitamente definidas por ambiente em `settings.py`.

## Arquitetura Alvo
## 1) Matriz Unica de Acesso
Criar uma matriz central "recurso -> permissao" para:
- menu item (`name/url_name`)
- view route (funcao/classe)
- endpoint API (DRF e views JSON)

Formato alvo (arquivo de configuracao):
- recurso: identificador estavel (ex: `nota_fiscal.emitir_lista`)
- menu: `common/menu_config.py` referencia esse recurso
- backend: decorator/permissao DRF referencia mesmo recurso
- testes: usam a mesma matriz para validar cobertura

## 2) Enforcement Padronizado no Backend
Padrao para views HTML/JSON:
- `@login_required` ou `@login_required_json`
- `@permission_required('app.codename', raise_exception=True)` quando recurso exigir
- validacao de escopo de tenant/emitente quando aplicavel

Padrao para DRF:
- `permission_classes = [DjangoModelPermissions]` quando houver CRUD/lista de modelos
- `IsAuthenticated` apenas para endpoints genericos que nao exigem perm granular (casos raros e documentados)
- filtros sempre limitados por escopo permitido do usuario

## 3) Seguranca de Webhooks
Webhook externo deve exigir autenticidade:
- assinatura HMAC em header (recomendado)
- secret por ambiente em `.env`
- validacao de timestamp anti-replay
- resposta 401/403 para assinatura invalida
- logs de auditoria (sem vazar segredo)

## 4) Hardening de Sessao e Transporte
Controlar por ambiente (`DEBUG=False`):
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `SESSION_COOKIE_HTTPONLY=True`
- `CSRF_COOKIE_SAMESITE='Lax'` (ou `Strict` conforme impacto)
- `SESSION_COOKIE_SAMESITE='Lax'`
- `SECURE_SSL_REDIRECT=True` (quando HTTPS ativo)
- `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`

## 5) Auditoria e Telemetria
- log estruturado para tentativas 403 relevantes
- trilha minima: usuario, recurso, rota, metodo, host, tenant
- sem logar dados sensiveis (token, senha, payload sigiloso)

## Fases de Implementacao (Controlada)
## Fase 0 - Preparacao e Inventario
1. Consolidar inventario de rotas e endpoints.
2. Criar matriz inicial menu->rota->permissao.
3. Classificar recursos por criticidade (Alta/Media/Baixa).
4. Definir politica para endpoints publicos intencionais.

Entrega:
- documento de matriz versionado
- checklist de cobertura inicial

## Fase 1 - Fechamento de Brechas Criticas
1. Proteger webhook com assinatura.
2. Adicionar permissao nas views de listagem sensiveis sem quebrar fluxo AJAX.
3. Fechar endpoints publicos nao intencionais.
4. Aplicar `DjangoModelPermissions` nos ViewSets pendentes.

Entrega:
- brechas criticas mitigadas
- testes de autorizacao para casos negativos (403/401)

## Fase 2 - Padronizacao Completa
1. Migrar todas as rotas para matriz de permissao.
2. Remover inconsistencias entre permissoes de menu e backend.
3. Revisar prefixos de URL API e namespace para clareza de superficie exposta.
4. Padronizar respostas de erro de autorizacao (HTML e JSON).

Entrega:
- cobertura completa documentada
- validacao funcional por modulo

## Fase 3 - Hardening de Producao
1. Aplicar flags de seguranca por ambiente.
2. Revisar hosts/dominios e comportamento multi-tenant.
3. Executar checklist OWASP basico para app interno (auth, authz, sessao, input, logs).

Entrega:
- baseline de seguranca operacional

## Matriz de Trabalho (Template para preenchimento e marcacao)
Legenda:
- `INV`: inventariado
- `PERM`: permissao backend alinhada
- `TEN`: escopo tenant validado
- `API`: endpoint API protegido e validado
- `TEST`: teste de autorizacao criado/validado
- `OBS`: observacao/residuo

| Recurso | Menu | Rota/Endpoint | Permissao esperada | Criticidade | INV | PERM | TEN | API | TEST | OBS |
|---|---|---|---|---|---|---|---|---|---|---|
| Configuracoes > Lista de Usuarios | `accounts:lista_usuarios` | `accounts.views.lista_usuarios` | `accounts.view_user` | Alta | [x] | [x] | [x] | N/A | [x] | cobertura consolidada em matriz + testes de contrato |
| Configuracoes > Lista de Grupos | `accounts:lista_grupos` | `accounts.views.lista_grupos` | `auth.view_group` | Alta | [x] | [x] | [x] | N/A | [x] | cobertura consolidada em matriz + testes de contrato |
| Nota Fiscal > Emitir NF-e | `nota_fiscal:emitir_nfe_list` | `nota_fiscal.views.emitir_nfe_list_view` | `integracao_nfe.can_emit_nfe` | Alta | [x] | [x] | [x] | [x] | [x] | validado no endurecimento de emissao e contratos 403/401 |
| Nota Fiscal > Entradas | `nota_fiscal:entradas_nota` | `nota_fiscal.views.entradas_nota_view` | `nota_fiscal.view_notafiscal` | Alta | [x] | [x] | [x] | N/A | [x] | validado por testes e matriz central |
| Nota Fiscal > Criar NF-e Saida | `nota_fiscal:criar_nfe_saida` | `nota_fiscal.views.criar_nfe_saida` | `nota_fiscal.add_notafiscal` | Alta | [x] | [x] | [x] | N/A | [x] | validado por testes e matriz central |
| Relatorios > Notas de Entrada | `relatorios:notas_entradas` | `relatorios.views.notas_entradas_view` | `relatorios.view_notafiscalrelatorio` | Alta | [x] | [x] | [x] | N/A | [x] | contrato de permissao JSON padronizado e testado |
| Fiscal API CFOP | N/A | `common.api.fiscal.CfopViewSet` | `fiscal.*_cfop` | Media | [x] | [x] | [x] | [x] | [x] | cobertura de contrato 403/401 e matriz PATH |
| Produto API | N/A | `common.api.produto.ProdutoViewSet` | `produto.view_produto` | Alta | [x] | [x] | [x] | [x] | [x] | DjangoModelPermissionsWithView aplicado e testado |
| Item Nota API | N/A | `common.api.item_nota_fiscal.ItemNotaFiscalViewSet` | `nota_fiscal.view_itemnotafiscal` | Alta | [x] | [x] | [x] | [x] | [x] | DjangoModelPermissionsWithView aplicado e testado |
| Categoria Produto API | N/A | `produto.views.categoria_list_api` | autenticado + perm definida | Media | [x] | [x] | [x] | [x] | [x] | endpoint protegido com permissao explicita e teste de 403 |
| Controle Ping | N/A | `control.views.ping_view` | autenticado (`__auth_only__`) | Baixa | [x] | [x] | [x] | [x] | [x] | politica consolidada para healthcheck interno |
| Integracao webhook | N/A | `integracao_nfe.views.sefaz_webhook` | assinatura HMAC valida | Alta | [x] | [x] | [x] | [x] | [x] | HMAC + anti-replay + testes negativos |

## Lista de Arquivos-Alvo (por etapa)
Core de seguranca:
- `common/menu_config.py`
- `common/context_processors.py`
- `accounts/utils/decorators.py`
- `accounts/middleware.py`
- `config/settings.py`

Views HTML/JSON:
- `accounts/views.py`
- `nota_fiscal/views.py`
- `relatorios/views.py`
- `produto/views.py`
- `control/views.py`
- `integracao_nfe/views.py`

APIs:
- `common/api/produto.py`
- `common/api/item_nota_fiscal.py`
- `common/api/fiscal.py`
- `common/api/nota_fiscal.py`
- `common/api/urls.py`

URLs:
- `config/urls.py`
- `integracao_nfe/urls.py`
- `nota_fiscal/urls.py`
- `produto/urls.py`
- `relatorios/urls.py`
- `control/urls.py`

Testes (novos):
- `tests/security/test_permissions_matrix.py`
- `tests/security/test_api_authz.py`
- `tests/security/test_webhook_signature.py`
- `tests/security/test_tenant_host_isolation.py`

## Criterios de Aceite por Lote
1. Usuario sem permissao recebe 403 na rota direta.
2. Usuario sem permissao nao consegue consumir endpoint API protegido.
3. Menu apenas espelha backend (nunca substitui autorizacao).
4. Webhook invalido por assinatura retorna 401/403.
5. Fluxos autorizados continuam funcionais (sem regressao).
6. Sem erros no console e sem quebra do fluxo AJAX.

## Riscos e Mitigacoes
- Risco: regressao de acesso legitimo por permissao faltante.
  - Mitigacao: rollout por lote, matriz com checklist e teste negativo/positivo.
- Risco: impacto em ambiente local sem HTTPS nas flags de seguranca.
  - Mitigacao: condicionar flags por ambiente (`DEBUG`/variavel de ambiente).
- Risco: quebra de integracao externa no webhook.
  - Mitigacao: fase de compatibilidade com modo monitorado antes de bloqueio total.

## Sequencia Recomendada de Execucao
1. Webhook HMAC + testes.
2. Contas e relatorios (listas sensiveis).
3. Nota fiscal (views + APIs sensiveis + escopo emitente/tenant).
4. Produto/control (endpoints expostos).
5. Hardening de settings por ambiente.
6. Revisao final cruzada com plano de unificacao das listas.

## Integracao com o Plano de Unificacao das Listas
Este plano deve rodar em paralelo, com prioridade de seguranca:
- primeiro garantir autorizacao backend das telas listadas no plano de listas
- depois continuar migracao de UX/JS da lista
- cada tela so pode ser marcada como concluida no plano de listas se o item de permissao correspondente estiver ao menos com `PERM=[x]`

## Fechamento por Modulo (Status Atual)
Legenda:
- `OK`: implementado e validado por teste/comando
- `PARCIAL`: implementado, com decisao de produto/negocio pendente

| Modulo | Status | Evidencia principal |
|---|---|---|
| `accounts` | OK | `permission_required_json`, testes 401/403, log `security.authz` |
| `empresas` | OK | 403 JSON com `code`, testes de contrato API/HTML |
| `fiscal` | OK | controle de permissao + contrato 403, testes de exclusao protegida |
| `nota_fiscal` | OK | rotas criticas com permissao explicita e resposta padronizada |
| `relatorios` | OK | API com contrato `permission_denied`/`not_authenticated` |
| `integracao_nfe` | OK | webhook HMAC + anti-replay, validacoes de emissao por tenant |
| `control` | OK | `ping` autenticado + testes de isolamento por host/tenant |
| `common/api` | OK | handler DRF global + `DjangoModelPermissionsWithView` |
| `menu/matriz` | OK | `auditar_matriz_acesso` + teste automatizado |
| `hardening settings` | OK | flags `SECURE_*` e cookies por ambiente |
| `auditoria operacional` | OK | `auditar_seguranca` + `validar_baseline_seguranca` |
| `painel` | OK | permissao dedicada `painel.view_dashboard` aplicada na home com testes de acesso |

## Residuos e Pendencias Objetivas
1. [x] Politica final do modulo `painel` definida com permissao dedicada (`painel.view_dashboard`).
2. [ ] Definir parametros finais de producao para `USE_HTTPS=True` e executar `validar_baseline_seguranca --strict` no ambiente alvo.
3. [x] Pipeline CI adicionada para rodar `manage.py auditar_seguranca --strict` no stage de release (`.github/workflows/security-audit.yml`).

## Comando de Fechamento da Fase
- Auditoria padrao (ambiente atual):
  - `python manage.py auditar_seguranca`
- Auditoria estrita (gate de producao):
  - `python manage.py auditar_seguranca --strict`
