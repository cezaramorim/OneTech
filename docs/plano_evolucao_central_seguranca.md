# Plano de Evolucao da Central de Seguranca

- Data de criacao: 2026-03-13
- Ultima atualizacao: 2026-03-13
- Status: Planejado (aguardando inicio apos conclusao do plano atual)
- Escopo: Modulo Control + Telemetria comum + Auditoria operacional

## Objetivo
Evoluir a Central de Seguranca para operar como painel unico de monitoramento, auditoria e resposta, cobrindo:
- tentativas de acesso indevido
- trilha de acesso por usuario
- estado de sessoes ativas
- baseline e auditoria tecnica
- operacoes de resposta rapida

## Principios de Engenharia
1. Sem quebrar fluxo atual da Central.
2. Implementacao incremental por fase com rollback simples.
3. Backward compatibility de rotas e contratos JSON.
4. Sem scripts inline; reaproveitar pipeline global de JS.
5. Multi-tenant: respeitar contexto ativo e dominio principal/default.
6. Logs sempre persistidos sem falha silenciosa.

## Arquitetura Alvo
### Dados
- Reusar `control.SecurityAuditEvent` como trilha principal.
- Criar tabela dedicada para sessoes de seguranca (snapshot operacional), se necessario.
- Criar tabela opcional de alertas agregados (contador por janela de tempo).

### Backend
- Endpoints JSON dedicados para cards e listas da Central.
- Camada de servico para agregacao de metricas (24h/7d/30d).
- Contrato padrao para erros: `success=false`, `code`, `message`.

### Frontend
- Manter template padrao do projeto (partials + css/js dedicados).
- Atualizacao por fetch com feedback de carregamento.
- Filtros por periodo, usuario, evento, rota, tenant e status.

## Fases de Implementacao

## Fase 1 - Observabilidade Basica (prioridade alta)
1. [ ] Corrigir persistencia de eventos sem `except: pass` silencioso.
2. [ ] Registrar sempre `run_security_audit` (normal/strict) com user e host quando disponivel.
3. [ ] Adicionar evento de login com sucesso e login com falha.
4. [ ] Adicionar evento de logout e force logout.
5. [ ] Exibir filtros na grade de eventos recentes (data, usuario, codigo, rota).
6. [ ] Adicionar exportacao CSV dos eventos filtrados.
7. [ ] Testes automatizados para persistencia e listagem dos eventos.

Entregaveis Fase 1:
- `control/views.py` (endpoints e filtros)
- `common/security_audit.py` (persistencia robusta)
- `templates/partials/control/central_seguranca.html` (filtros e tabela)
- `static/control/js/central_seguranca.js` (consulta e interacao)
- `static/control/css/central_seguranca.css` (ajustes visuais)
- `control/tests.py` (cobertura)

## Fase 2 - Deteccao e Alertas (prioridade alta)
1. [ ] Painel de negacoes 401/403 por janela (24h/7d/30d).
2. [ ] Alertar bursts de negacao por IP/usuario/rota.
3. [ ] Alertar tentativas repetidas de acesso a endpoint sensivel.
4. [ ] Painel de origem (host/ip) com top ofensores.
5. [ ] Painel de risco por tenant (quando em dominio tenant).
6. [ ] Botao de abrir detalhes do alerta (drill-down).
7. [ ] Testes de agregacao e contratos de alerta.

Entregaveis Fase 2:
- `control/services/security_metrics.py` (novo)
- `control/views.py` (novos endpoints JSON)
- `static/control/js/central_seguranca.js` (cards dinamicos)
- `control/tests.py` (agregacao/contrato)

## Fase 3 - Resposta Operacional (prioridade media)
1. [ ] Encerrar sessoes por usuario (ja existente) com auditoria detalhada.
2. [ ] Encerrar todas as sessoes de um usuario com confirmacao reforcada.
3. [ ] Bloqueio temporario de usuario (cooldown) com expiracao.
4. [ ] Quarentena de tenant (modo leitura) para incidente.
5. [ ] Historico de acoes administrativas da Central.
6. [ ] Testes de permissao para cada acao de resposta.

Entregaveis Fase 3:
- `control/views.py`
- `control/models.py` (se houver novos estados)
- `control/forms.py` (se necessario)
- `control/tests.py`

## Fase 4 - Vulnerabilidades e Compliance (prioridade media)
1. [ ] Integrar resultado de `pip-audit` no painel (ultimo run).
2. [ ] Exibir status de baseline strict com historico.
3. [ ] Exibir divergencias menu x matriz com resumo tecnico.
4. [ ] Exportar relatorio consolidado (JSON/CSV).
5. [ ] Preparar endpoint para integracao SIEM futuro.

Entregaveis Fase 4:
- `control/management/commands/*` (adaptacoes)
- `control/views.py`
- `templates/partials/control/central_seguranca.html`
- `control/tests.py`

## Checklist de Seguranca Funcional da Central
1. [ ] Usuario comum nao acessa Central.
2. [ ] Usuario comum nao executa auditoria.
3. [ ] Usuario comum nao encerra sessoes de terceiros.
4. [ ] Superuser executa auditoria normal/strict com retorno visivel.
5. [ ] Erros tecnicos exibem mensagem e nao deixam UI travada.
6. [ ] Eventos sao persistidos mesmo com falha parcial de contexto.
7. [ ] Nenhum endpoint da Central responde sem autenticacao.

## Plano de Testes
1. Testes unitarios
- persistencia de evento
- agregacao de metricas
- filtros e paginacao

2. Testes de integracao
- fluxo auditoria normal
- fluxo auditoria strict reprovada
- fluxo force logout

3. Testes de permissao
- superuser vs usuario comum
- dominio default vs dominio tenant

## Riscos e Mitigacoes
1. Risco: crescimento rapido da tabela de eventos.
- Mitigacao: retencao por janela e indice por `created_at`, `code`, `user`.

2. Risco: falha silenciosa de log.
- Mitigacao: remover swallow de excecao e registrar erro tecnico em logger dedicado.

3. Risco: regressao de performance na tela.
- Mitigacao: consultas paginadas e agregacoes em servico com limites.

## Ordem de Execucao Recomendada (quando iniciar)
1. Fase 1 completa
2. Fase 2 completa
3. Fase 3 completa
4. Fase 4 completa

## Criterio de Pronto
- Todas as tarefas da fase marcada como concluida.
- Testes da fase passando.
- Validacao manual em ambiente local (default + tenant).
- Sem erros no console e sem caracteres invalidos na UI.