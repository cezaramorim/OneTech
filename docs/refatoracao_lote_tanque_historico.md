# Refatoracao Lote x Tanque (Historico de Execucao) 09/03/2026

## Objetivo
Padronizar o projeto para separar corretamente:
- estado atual: `Lote.tanque_atual`
- historico por data: `LoteDiario.tanque` e `EventoManejo.tanque_origem/tanque_destino`

## Regra de negocio acordada
- Um lote pode mudar de tanque a qualquer momento.
- O historico deve refletir o tanque do dia/evento, nao o tanque atual.
- Nomes de lote podem se repetir; identidade tecnica deve usar `lote.id`.

## Estado inicial mapeado
- Modelos:
  - `Lote.tanque_atual` existe.
  - `LoteDiario.tanque` existe.
  - `EventoManejo.tanque_origem/tanque_destino` existe.
- Problema principal:
  - Telas e APIs historicas ainda usam `lote.tanque_atual` em varios pontos.

## Alteracoes ja concluidas antes desta refatoracao
1. Correcao de filtro de eventos em arracoamento: `data__lte` -> `data_evento__lte`.
2. Correcao de modal de ambiente (payload `{ success, fases }`).
3. Correcao de edicao para `quantidade_kg` no modal.
4. Correcao de interceptacao global do botao editar (nao abrir JSON no `main-content`).
5. Fallback de aprovacao usando `sugestao.quantidade_kg` quando ajustada nao existir.
6. Hardening da exclusao em lote (ids validos, ids faltantes/invalidos).
7. Mensagens de exclusao parcial em UI e backend.
8. Remocao de rota duplicada `api/fases-com-tanques/`.
9. Move do script para `producao/static/producao/js/arracoamento_diario.js`.

## Plano de execucao da refatoracao (incremental)
1. Arracoamento Diario:
   - Preferir `lote_diario.tanque` para exibicao/ordenacao/filtro por linha.
   - Manter fallback para `lote.tanque_atual` quando snapshot nao existir.
2. APIs/listas historicas:
   - Revisar views historicas para evitar leitura por `lote.tanque_atual`.
3. Integridade de snapshot:
   - Garantir preenchimento consistente de `LoteDiario.tanque` nas rotinas de recalculo/reprojecao.
4. Limpeza de dados legados:
   - Tratar `LoteDiario` anterior ao `data_povoamento` sem apagar dados produtivos de forma cega.

## Registro de andamento
### 2026-03-05 - Inicio formal da refatoracao
- Historico formal criado.
- Proximo passo em execucao: item 1 (Arracoamento Diario).

### 2026-03-05 - Passo 1 concluido (Arracoamento Diario)
- API de sugestoes passou a priorizar lote_diario.tanque (com fallback para lote.tanque_atual).
- Ajustados: select_related, filtro por linha de producao, ordenacao por sequencia e campos serializados (tanque/linha/sequencia).
- Validacao tecnica: env\\Scripts\\python.exe -m py_compile producao\\views_arracoamento.py sem erro.
- Proximo passo: tratar pendencias anteriores considerando data_povoamento do lote (evitar falso pendente legado).

### 2026-03-05 - Passo 2 concluido (Pendencias anteriores)
- Regra de pendencias agora considera somente periodo valido do lote (data_evento >= data_povoamento).
- Quando existe ultimo realizado, inicio da janela usa max(ultimo_realizado + 1 dia, data_povoamento).
- Objetivo: eliminar falso pendente vindo de LoteDiario legado anterior ao povoamento.
- Validacao tecnica: env\\Scripts\\python.exe -m py_compile producao\\views_arracoamento.py sem erro.

### 2026-03-05 - Passo 3 concluido (Saneamento legado de datas)
- Comando criado: udit_lotediario_legacy (auditoria e opcao --fix).
- Execucao de saneamento aplicada com --fix.
- Verificacao sequencial apos limpeza: Nenhum LoteDiario legado encontrado.


### 2026-03-05 - Passo 4 concluido (Historico de eventos por tanque do evento)
- Endpoint ajustado: pi_ultimos_eventos.
- Filtros de unidade/linha agora priorizam 	anque_origem e 	anque_destino do proprio evento.
- Mantido fallback legado para lote.tanque_atual apenas quando o evento antigo nao possui tanque de origem/destino.
- Troca tecnica de prefetch_related para select_related em FKs do endpoint.
- Validacao tecnica: env\\Scripts\\python.exe -m py_compile producao\\views.py sem erro.

### 2026-03-05 - Passo 5 concluido (Historico de povoamento com tanque historico)
- Endpoint ajustado: historico_povoamento_view.
- Leitura agora inclui 	anque_origem e 	anque_destino no select_related.
- Campo 	anque_nome passou a priorizar: 	anque_destino -> 	anque_origem -> fallback legado em lote.tanque_atual.
- Incluidos no payload os campos 	anque_origem_nome e 	anque_destino_nome (sem quebrar contrato atual).
- Validacao tecnica: env\\Scripts\\python.exe -m py_compile producao\\views.py sem erro.

### 2026-03-05 - Passo 6 concluido (Integridade de snapshot LoteDiario.tanque)
- Criado helper: obter_tanque_lote_em_data(lote, data_referencia) em producao/utils.py.
- Regra do helper: prioriza tanques do proprio evento (	anque_origem/	anque_destino) e usa lote.tanque_atual apenas como fallback legado.
- Reprojecao (
eprojetar_ciclo_de_vida) agora grava/atualiza LoteDiario.tanque com base historica da data.
- API de sugestoes do arracoamento (pi_sugestoes_arracoamento) agora sincroniza LoteDiario.tanque ao iterar cada dia.
- Validacao tecnica: env\\Scripts\\python.exe -m py_compile producao\\utils.py producao\\views_arracoamento.py sem erro.

### 2026-03-05 - Passo 7 concluido (Comando de backfill de snapshot de tanque)
- Novo comando: ackfill_lotediario_tanque em producao/management/commands/backfill_lotediario_tanque.py.
- Modo auditoria por padrao; modo aplicacao via --apply.
- Regras: preenche apenas LoteDiario.tanque nulo, sem alterar outros campos.
- Auditoria executada: 886 candidatos, 886 elegiveis para preenchimento, 0 sem resolucao.

### 2026-03-05 - Passo 8 concluido (Transferencia com tanque de origem por data)
- Ajustada RegistrarEventoView para resolver 	anque_origem pela data do evento.
- Antes: 	anque_origem_obj = lote_origem.tanque_atual.
- Agora: 	anque_origem_obj = obter_tanque_lote_em_data(lote_origem, evento.data_evento).
- Beneficio: lancamentos retroativos de transferencia passam a gravar tanque de origem historico correto no EventoManejo.
- Validacao tecnica: env\\Scripts\\python.exe -m py_compile producao\\views.py sem erro.

### 2026-03-05 - Passo 9 concluido (Fallback historico no historico_povoamento)
- Ajustado fallback de tanque em historico_povoamento_view para usar obter_tanque_lote_em_data(lote, data_evento).
- Antes: fallback usava lote.tanque_atual (estado atual).
- Agora: fallback resolve tanque do dia do evento (historico real), mantendo prioridade 	anque_destino -> 	anque_origem.
- Validacao tecnica: env\\Scripts\\python.exe -m py_compile producao\\views.py sem erro.

### 2026-03-05 - Passo 10 concluido (API lote por tanque com data opcional)
- Endpoint ajustado: get_active_lote_for_tanque_api.
- Novo comportamento opcional: aceita ?data_evento=YYYY-MM-DD para retornar lote do tanque naquela data (via LoteDiario).
- Comportamento legado preservado: sem data_evento, continua retornando lote ativo atual (	anque_atual).
- Beneficio: suporte a consultas historicas sem quebrar chamadas existentes do frontend.
- Validacao tecnica: env\\Scripts\\python.exe -m py_compile producao\\views.py sem erro.

### 2026-03-05 - Passo 11 concluido (Otimização de desempenho do tanque historico)
- Criado resolvedor em memoria por lote: construir_resolvedor_tanque_lote em producao/utils.py.
- Reprojecao (
eprojetar_ciclo_de_vida) agora reutiliza resolvedor por lote (evita consulta de evento por dia).
- API de sugestoes (pi_sugestoes_arracoamento) agora reutiliza resolvedor por lote durante loop diario.
- Backfill (ackfill_lotediario_tanque) agora reutiliza resolvedor por lote ao iterar registros nulos.
- Validacoes:
  - env\\Scripts\\python.exe -m py_compile producao\\utils.py producao\\views_arracoamento.py producao\\management\\commands\\backfill_lotediario_tanque.py
  - Auditoria backfill segue normal: nenhum LoteDiario.tanque nulo.
  - Comparacao amostral: resolvedor em memoria = funcao direta (OK True).

### 2026-03-05 - Passo 12 concluido (Cache por lote no historico_povoamento)
- historico_povoamento_view passou a usar cache de resolvedor historico por lote (
esolvedores_tanque).
- Evita repetir resolucao por evento quando ha varios registros do mesmo lote no periodo.
- Contrato de resposta mantido.
- Validacao tecnica: env\\Scripts\\python.exe -m py_compile producao\\views.py e teste endpoint /producao/api/historico-povoamento/ com 200.
