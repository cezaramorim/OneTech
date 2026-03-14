# Plano Global de Padronizacao de Listas v2 10/03/2026

- Data de criacao: 2026-03-10
- Ultima atualizacao: 2026-03-12 (Fase 3 concluida: arracoamento_diario migrado para contrato unificado de acoes; escopo principal e Producao 100% migrados)
- Status: Concluido

## Objetivo
Criar um padrao unico, previsivel e reutilizavel para telas de listagem com:
- busca
- limpar
- selecao por linha
- selecionar todos
- editar selecionado
- excluir selecionados

A migracao sera controlada, sem lote massivo, com rastreio de residuos (logica antiga) ate eliminacao final.

## Principios Tecnicos
- eficiencia: um motor JS unico por delegacao, sem bind duplicado
- escalabilidade: contrato HTML padrao por tela
- manutenabilidade: comportamento concentrado em um modulo unico
- usabilidade: respostas imediatas, estado de botoes consistente, feedback de acao
- semantica: ids/classes/data-attrs padronizados
- robustez: anti-race em navegacao AJAX e regras claras de migracao

## Mapeamento do Estado Atual (Codigo Existente)
### Motor A (legado generico por `#identificador-tela`) [REMOVIDO]
- arquivo: `static/js/scripts.js`
- funcoes: `updateButtonStates`, handlers globais para `#btn-editar` e `#btn-excluir`
- contrato: `data-url-editar`, `data-url-excluir`, `data-seletor-checkbox`, `data-seletor-pai`
- status: removido do fluxo global; nenhuma dependencia ativa identificada

### Motor B (delegacao unificada de listas)
- arquivo: `static/js/scripts.js`
- funcoes: `initFiscalList`, `initFiscalListDelegation`
- contrato: `data-list-controller="unified-list"`, `#search-input`, `#btn-limpar-busca`, `.row-checkbox`, `#select-all-checkbox`, `#btn-editar-selecionado`, `#btn-excluir-selecionados`
- status: ativo e estavel para telas migradas

### Motor C (modulos por tela)
- arquivo: `static/js/scripts.js` + JS especificos
- status: mantido apenas para comportamentos de negocio que nao sao de listagem

## Estrategia de Migracao e Residuo
## Fase 0 - Preparacao
- consolidar especificacao no `scripts.js`
- nao remover legado nesta fase

## Fase 1 - Migracao por tela
1. adequar contrato HTML para `data-list-controller="unified-list"`
2. garantir ids/classes padrao
3. validar fluxo completo
4. marcar checklist: `MIG` e `RES`

## Fase 2 - Limpeza de residuos
- remover blocos legados locais apos validacao por tela
- cada remocao com commit focado e checagem regressiva

## Fase 3 - Migracao do legado Producao (Motor A)
- objetivo: migrar telas de `producao/` que ainda dependem de contrato antigo
- regra de seguranca:
- nao remover globalmente `updateButtonStates` enquanto houver tela com `MIG=[ ]`
- confirmar uso antes de cada exclusao de trecho legado
- status: concluida em 2026-03-12

## Regra de Ouro
Nenhuma tela pode ser marcada como concluida sem:
- `MIG=[x]` (migrada no contrato unificado)
- `RES=[x]` (residuo legado removido ou inexistente para a tela)

## Matriz de Checklist (Escopo Principal)
Legenda:
- `MIG`: migrada e validada no motor unificado
- `RES`: residuo legado removido da tela
- `N/A`: fora do contrato de lista unificada

| Modulo | Template | Motor atual | MIG | RES | OBS |
|---|---|---|---|---|---|
| Fiscal | `templates/partials/fiscal/cfop_list.html` | B | [x] | [x] | validada; sem residuo local especifico |
| Fiscal | `templates/partials/fiscal/natureza_operacao_list.html` | B | [x] | [x] | validada; sem residuo local especifico |
| Fiscal Regras | `templates/partials/fiscal_regras/regra_icms_list.html` | B | [x] | [x] | validada; sem residuo local especifico |
| Comercial | `templates/comercial/condicao_pagamento_list.html` | C | [x] | [x] | validada; residuo legado removido |
| Empresas | `templates/partials/empresas/lista_empresas.html` | A + C | [x] | [x] | validada; residuo legado local removido |
| Empresas | `templates/partials/empresas/lista_categorias.html` | A/C | [x] | [x] | validada; sem residuo local especifico |
| Produtos | `templates/partials/produtos/lista_produtos.html` | A/C | [x] | [x] | validada; sem residuo local especifico |
| Produtos | `templates/partials/produtos/lista_categorias.html` | A/C | [x] | [x] | validada; sem residuo local especifico |
| Produtos | `templates/partials/produtos/lista_unidades.html` | A/C | [x] | [x] | validada; sem residuo local especifico |
| Nota Fiscal | `templates/partials/nota_fiscal/emitir_nfe_list.html` | C | [x] | [x] | validada; modulo de emissao mantido |
| Nota Fiscal | `templates/partials/nota_fiscal/entradas_nota.html` | C | [x] | [x] | validada; sem residuo local especifico |
| Relatorios | `templates/partials/relatorios/notas_entradas.html` | C | [x] | [x] | validada; residuo legado removido |
| Accounts | `templates/partials/accounts/lista_usuarios.html` | A/C | [x] | [x] | validada; sem residuo local especifico |
| Accounts | `templates/partials/accounts/lista_grupos.html` | A/C | [x] | [x] | validada; sem residuo local especifico |
| Control | `templates/partials/control/tenant_list.html` | C | [x] | [x] | validada; sem residuo local especifico |
| Control | `templates/partials/control/lista_emitentes.html` | C | [x] | [x] | validada; residuo legado removido |
| Control | `templates/partials/control/central_migracoes.html` | C | [x] | [x] | N/A: painel operacional |

## Status da Fase 1
- Situacao: concluida para telas elegiveis ao contrato de lista unificada.
- Pendencia remanescente: nenhuma no escopo de listas.

## Matriz de Checklist - Fase 3 (Producao Legado)
| Modulo | Template | Motor atual | MIG | RES | OBS |
|---|---|---|---|---|---|
| Producao | `producao/templates/producao/tanques/lista_tanques.html` | A -> Unificado | [x] | [x] | lote 1: contrato unificado + residuo local removido |
| Producao | `producao/templates/producao/lotes/lista_lotes.html` | A -> Unificado | [x] | [x] | lote 1: contrato unificado |
| Producao | `producao/templates/producao/eventos/lista_eventos.html` | A -> Unificado | [x] | [x] | lote 1: contrato unificado; filtros mantidos |
| Producao | `producao/templates/producao/curvas/lista_curvas.html` | A -> Unificado | [x] | [x] | lote 2: contrato unificado |
| Producao | `producao/templates/producao/suporte/faseproducao_list.html` | A -> Unificado | [x] | [x] | lote 2: contrato unificado |
| Producao | `producao/templates/producao/suporte/linhaproducao_list.html` | A -> Unificado | [x] | [x] | lote 2: contrato unificado |
| Producao | `producao/templates/producao/suporte/malha_list.html` | A -> Unificado | [x] | [x] | lote 2: contrato unificado |
| Producao | `producao/templates/producao/suporte/statustanque_list.html` | A -> Unificado | [x] | [x] | lote 3: contrato unificado |
| Producao | `producao/templates/producao/suporte/tipoevento_list.html` | A -> Unificado | [x] | [x] | lote 3: contrato unificado |
| Producao | `producao/templates/producao/suporte/tipotanque_list.html` | A -> Unificado | [x] | [x] | lote 3: contrato unificado |
| Producao | `producao/templates/producao/suporte/tipotela_list.html` | A -> Unificado | [x] | [x] | lote 3: contrato unificado |
| Producao | `producao/templates/producao/suporte/unidade_list.html` | A -> Unificado | [x] | [x] | lote 4 em 2026-03-11: contrato unificado aplicado |
| Producao | `producao/templates/producao/arracoamento_diario.html` | C (JS especifico + contrato unificado de acoes) | [x] | [x] | migrado: sem dependencia de `data-url-*`/`data-seletor-checkbox` do legado |

## Definicao de Pronto por Tela
Uma tela recebe `MIG=[x]` quando:
1. busca/filtro funciona sem reload manual extra
2. limpar funciona
3. editar selecionado funciona com 1 item
4. excluir selecionados funciona com confirmacao
5. botoes refletem estado de selecao
6. sem erro no console
7. sem script inline novo

Uma tela recebe `RES=[x]` quando:
1. bindings antigos nao executam para a tela
2. atributos legados nao sao mais necessarios
3. regressao basica aprovada

## Governanca de Entrega
- um commit por lote/tela validado
- diff pequeno e focado
- checklist atualizado no mesmo commit
- sem migracao em massa fora do lote combinado
- sem remover legado global antes de concluir toda Fase 3

