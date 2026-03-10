# Plano Global de Padronizacao de Listas v2 10/03/2026

- Data de criacao: 2026-03-10
- Ultima atualizacao: 2026-03-10


## Objetivo
Criar um padrao unico, previsivel e reutilizavel para telas de listagem com:
- busca
- limpar
- selecao por linha
- selecionar todos
- editar selecionado
- excluir selecionados

A migracao sera controlada, sem lote, com rastreio de residuos (logica antiga) ate eliminacao final.

## Principios Tecnicos
- eficiencia: um motor JS unico por delegacao, sem bind duplicado
- escalabilidade: contrato HTML padrao por tela
- manutenabilidade: comportamento concentrado em um modulo unico
- usabilidade: respostas imediatas, estado de botoes consistente, feedback de acao
- semantica: ids/classes/data-attrs padronizados
- robustez: anti-race em navegacao AJAX e regras claras de migracao

## Mapeamento do Estado Atual (Codigo Existente)
### Motor A (legado generico por `#identificador-tela`)
- arquivo: `static/js/scripts.js`
- funcoes: `updateButtonStates`, handlers globais para `#btn-editar` e `#btn-excluir`
- contrato: `data-url-editar`, `data-url-excluir`, `data-seletor-checkbox`, `data-seletor-pai`
- status: funcional em telas legadas, mas fora do novo padrao fiscal

### Motor B (novo parcial de listas fiscais)
- arquivo: `static/js/scripts.js`
- funcoes: `initFiscalList`, `initFiscalListDelegation`
- contrato: `data-page`, `data-list-url`, `#search-input`, `#btn-limpar-busca`, `.row-checkbox`, `#select-all-checkbox`, `#btn-editar-selecionado`, `#btn-excluir-selecionados`
- status:
  - busca: implementada
  - limpar: implementada
  - selecao: implementada
  - editar selecionado: implementado
  - excluir selecionados: botao habilita/desabilita, mas nao ha handler de clique dedicado no motor B

### Motor C (modulos por tela)
- arquivo: `static/js/scripts.js` + JS especificos
- exemplos: `initListaEmpresas`, `initNcmMaintenance`, `initListaEmitentes`, etc.
- status: util para casos especiais, mas com sobreposicao de logica de lista entre telas

## Problema Estrutural Atual
- coexistencia de multiplos motores para a mesma responsabilidade
- divergencia de ids/classes/data-attrs entre telas
- risco de regressao em reload parcial AJAX
- ausencia de um fluxo unico de exclusao em lote no padrao novo

## Arquitetura Alvo (Novo Motor Unico)
## 1) Contrato HTML Unico por Lista
Raiz da lista:
- `data-page="<slug_da_lista>"`
- `data-list-url="<url_da_propria_lista>"`
- `data-list-controller="unified-list"` (novo marcador explicito)

Controles padrao:
- busca: `#search-input`
- limpar: `#btn-limpar-busca`
- linha: `.row-checkbox`
- selecionar todos: `#select-all-checkbox`
- editar: `#btn-editar-selecionado` com `data-edit-url-base`
- excluir: `#btn-excluir-selecionados` com:
  - `data-delete-url`
  - `data-item-type`
  - `data-entity-label-singular`
  - `data-entity-label-plural`

## 2) Novo Modulo JS em `static/js/scripts.js` (faseada)
Nome alvo: `UnifiedListController` (namespace interno, sem inline script)

Responsabilidades:
- bind unico por delegacao no `document.body`
- resolver `pageRoot` por `closest([data-list-controller="unified-list"])`
- busca com debounce configuravel
- Enter busca imediata
- Escape limpa e busca imediata
- limpar por botao com reset de filtros
- sincronizacao de estado de botoes por quantidade selecionada
- editar selecionado (somente 1 item)
- excluir selecionados (1+ itens) com confirmacao e reload via `loadAjaxContent`
- tratamento de erro padrao (toast/Swal)

API interna planejada:
- `initUnifiedListDelegation()`
- `resolveListRoot(element)`
- `buildListUrl(root, searchValue)`
- `updateSelectionState(root)`
- `executeSearch(root, value, immediate)`
- `executeEditSelected(root)`
- `executeDeleteSelected(root)`

## 3) Anti-race e Confiabilidade AJAX
Estado atual ja possui controle sequencial em `loadAjaxContent`.
Padrao v2 adiciona:
- cancelamento de debounce pendente por raiz
- descarte de eventos fora do contexto da tela ativa
- sem dependencia de script inline em templates

## 4) Backend de Busca por Relevancia (quando aplicavel)
Regra padrao:
1. match exato
2. startswith
3. contains
4. ordenacao secundaria configurada na tela

CFOP ja segue esse caminho e sera referencia para outras listas que precisarem.

## Estrategia de Migracao e Residuo
## Fase 0 - Preparacao (sem migrar telas)
- consolidar especificacao no `scripts.js` (novo modulo, desligado por default)
- nao remover legado nesta fase

## Fase 1 - Migracao por tela (controlada)
Para cada tela:
1. adequar contrato HTML para `data-list-controller="unified-list"`
2. garantir ids/classes padrao
3. habilitar tela no novo modulo
4. validar fluxo completo
5. marcar checklist:
   - `MIG` (migrada)
   - `RES` (residuo removido)

## Fase 2 - Limpeza de residuos
- apos conjunto minimo estavel de telas migradas, remover rotas de codigo legado por bloco
- cada remocao com commit dedicado e validacao regressiva

## Regra de Ouro
Nenhuma tela pode ser marcada como concluida sem marcar explicitamente os dois estados:
- migrada no novo motor
- residuo antigo removido (ou justificativa de bloqueio)

## Matriz de Checklist (Obrigatorio atualizar a cada etapa)
Legenda:
- `MIG`: migrada e validada no novo motor
- `RES`: residuo legado removido da tela
- `OBS`: motivo se ainda pendente

| Modulo | Template | Motor atual | MIG | RES | OBS |
|---|---|---|---|---|---|
| Fiscal | `templates/partials/fiscal/cfop_list.html` | B | [ ] | [ ] | |
| Fiscal | `templates/partials/fiscal/natureza_operacao_list.html` | B | [ ] | [ ] | |
| Fiscal Regras | `templates/partials/fiscal_regras/regra_icms_list.html` | B | [ ] | [ ] | |
| Comercial | `templates/comercial/condicao_pagamento_list.html` | C | [ ] | [ ] | validar caminho final |
| Empresas | `templates/partials/empresas/lista_empresas.html` | A + C | [ ] | [ ] | |
| Empresas | `templates/partials/empresas/lista_categorias.html` | A/C | [ ] | [ ] | mapear controles atuais |
| Produtos | `templates/partials/produtos/lista_produtos.html` | A/C | [ ] | [ ] | mapear controles atuais |
| Produtos | `templates/partials/produtos/lista_categorias.html` | A/C | [ ] | [ ] | mapear controles atuais |
| Produtos | `templates/partials/produtos/lista_unidades.html` | A/C | [ ] | [ ] | mapear controles atuais |
| Nota Fiscal | `templates/partials/nota_fiscal/emitir_nfe_list.html` | C | [ ] | [ ] | tabela + filtros |
| Nota Fiscal | `templates/partials/nota_fiscal/entradas_nota.html` | C | [ ] | [ ] | confirmar existencia |
| Relatorios | `templates/partials/relatorios/notas_entradas.html` | C | [ ] | [ ] | |
| Accounts | `templates/partials/accounts/lista_usuarios.html` | A/C | [ ] | [ ] | |
| Accounts | `templates/partials/accounts/lista_grupos.html` | A/C | [ ] | [ ] | |
| Control | `templates/partials/control/tenant_list.html` | C | [ ] | [ ] | mapear filtros |
| Control | `templates/partials/control/lista_emitentes.html` | C | [ ] | [ ] | |
| Control | `templates/partials/control/central_migracoes.html` | C | [ ] | [ ] | mapear filtros |

## Definicao de Pronto por Tela
Uma tela so recebe `MIG=[x]` quando:
1. busca funciona sem reload manual
2. limpar funciona sempre
3. editar selecionado funciona com 1 item
4. excluir selecionados funciona com confirmacao e retorno visual
5. botoes refletem estado de selecao corretamente
6. sem erro no console
7. sem script inline novo

Uma tela so recebe `RES=[x]` quando:
1. bindings antigos nao executam para essa tela
2. atributos legados nao sao mais necessarios
3. regressao basica da tela aprovada

## Logica de Implementacao no `scripts.js` (resumo executavel)
1. introduzir `UnifiedListController` sem quebrar motores A/B
2. bind global unico para:
   - `input` em `#search-input`
   - `keydown` em `#search-input`
   - `click` em `#btn-limpar-busca`
   - `click` em `#btn-editar-selecionado`
   - `click` em `#btn-excluir-selecionados`
   - `change` em `#select-all-checkbox` e `.row-checkbox`
3. usar `data-list-url` para busca (nunca `window.location` como fonte principal)
4. exclusao:
   - coletar ids marcados
   - abrir confirmacao
   - POST JSON para `data-delete-url`
   - recarregar lista por `loadAjaxContent` (ou `redirect_url`)
5. logica de estado unificada para habilitar/desabilitar botoes

## Governanca de Entrega
- um commit por tela migrada
- diff pequeno e focado
- checklist atualizado no mesmo commit da tela
- sem migracao em massa
- sem remover legado global antes de validar migracoes iniciais
