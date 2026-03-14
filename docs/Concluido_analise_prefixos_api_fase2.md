# Analise de Prefixos de API (Fase 2)

- Data de criacao: 2026-03-13
- Ultima atualizacao: 2026-03-14
- Status: Concluido (fase de analise e diretriz finalizadas)
- Escopo: revisar padrao de prefixos de API e propor convergencia sem regressao.

## Diagnostico atual

1. Existem APIs versionadas em prefixos diferentes:
- Global: `/api/v1/...` (via `common/api/urls.py` em `config/urls.py`)
- Por modulo: `/nota-fiscal/api/v1/...`, `/produtos/api/v1/...`, `/empresas/api/v1/...`, `/relatorios/api/v1/...`

2. Existem APIs operacionais sem versao em modulos:
- Ex.: `/producao/api/...`, `/nota-fiscal/api/...`, `/fiscal-regras/api/...`

3. Existe duplicidade de dominio funcional para notas:
- `/api/v1/notas-entradas/` (common)
- `/nota-fiscal/api/v1/notas-entradas/` (router local no modulo nota_fiscal)

## Riscos

- Ambiguidade de superficie exposta (mesmo recurso em mais de um prefixo).
- Maior custo de manutencao de clientes (frontend/integracoes) por pluralidade de caminhos.
- Maior chance de divergir politica de permissao entre endpoints equivalentes.

## Diretriz proposta (sem breaking change imediato)

1. Canonico de APIs versionadas:
- Manter **somente** `/api/v1/...` como canonico para recursos DRF compartilhados.

2. APIs operacionais de tela (AJAX interno):
- Manter no modulo, mas padronizar como `/modulo/api/...` e documentar como "nao-publicas".

3. Estrategia de migracao em 2 etapas:
- Etapa A (compat): manter rotas atuais + marcar alias como legadas em documentacao.
- Etapa B (cleanup): remover aliases apos validacao e janela de deprecacao.

## Itens de acao recomendados

1. Consolidar endpoints versionados de Nota Fiscal no `common/api` e remover router duplicado em `nota_fiscal/urls.py` apos etapa de compat.
2. Avaliar mover `/produtos/api/v1/produtos/` e `/empresas/api/v1/fornecedores/` para arvore global `/api/v1/...` (com redirecionamento/alias temporario).
3. Criar documento de "API canonica x alias legado" e usar em testes de regressao.
4. Garantir que aliases legados preservem exatamente o mesmo controle de permissao.

## Decisao para esta fase

- Nesta fase (Fase 2 parcial), **nao** alterar prefixos em runtime.
- Apenas registrar baseline, convergencia alvo e preparar migracao controlada.


## Encerramento da fase de analise
- A entrega desta fase era diagnosticar, definir diretriz e listar estrategia de migracao sem breaking change imediato.
- Esta entrega foi concluida em 2026-03-14.
- A execucao tecnica da convergencia de prefixos (cleanup de aliases) deve ser tratada em um plano de implementacao separado.
