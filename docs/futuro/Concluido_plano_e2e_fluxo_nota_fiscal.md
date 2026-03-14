# Plano E2E - Fluxo Completo de Nota Fiscal

- Data de criacao: 2026-03-14
- Status: Concluido (com 1 dependencia operacional externa)
- Escopo: automacao E2E do fluxo de edicao/emissao de NF

## Objetivo
Garantir validacao ponta a ponta (tela + backend) para reduzir regressao funcional no fluxo de nota fiscal.

## Escopo funcional E2E
1. Login e acesso ao modulo de Nota Fiscal.
2. Listagem de emissao com busca, limpar, editar selecionado.
3. Edicao da nota:
- Dados da nota (emitente, destinatario, tipo operacao, condicao pagamento).
- Produtos (busca, preenchimento automatico, totais).
- Duplicatas (geracao conforme condicao).
- Transporte.
4. Salvamento e retorno para listagem com dados atualizados.
5. Reabertura da nota para validar persistencia dos campos.

## Itens adicionais obrigatorios
1. Caso de permissao sem `fiscal_regras.override_aliquota_item`.
2. Caso de permissao com `fiscal_regras.override_aliquota_item`.
3. Fluxo de importacao XML com preview e processamento.
4. Mensagens de erro amigaveis quando API/servidor indisponivel.
5. Integracao com pipeline CI para bloquear merge quando E2E falhar.
6. Registro de evidencias por execucao (log + screenshots + status da build).
7. CI base de testes Django em push/PR (pre-requisito para evolucao do job E2E dedicado).

## Criterio de pronto
- Suite E2E executando local sem falha.
- Evidencia de execucao (log + screenshots) salva em `docs/futuro/snapshots/e2e_nf/`.
- Execucao automatica no CI com status obrigatorio para aprovacao.
- Checklist abaixo 100% marcado.

## Checklist
- [x] Estruturar testes E2E (framework e setup).
- [x] Implementar fluxo de emissao/edicao completo.
- [x] Implementar fluxo de importacao XML.
- [x] Implementar cenarios de permissao de override.
- [x] Implementar cenarios de erro de rede/servidor.
- [x] Gerar evidencias de execucao.
- [x] Rodar em ambiente default e tenant (contrato de selecao do emitente ativo validado em teste dedicado sem conexao dinamica de alias em runner local).
- [x] Publicar workflow CI para E2E de Nota Fiscal (`.github/workflows/e2e-nota-fiscal.yml`).
- [ ] Tornar job E2E obrigatorio no branch principal (acao manual no GitHub: Branch protection / Required status checks).
- [x] Publicar workflow CI base para testes Django em push/PR (`.github/workflows/ci-tests.yml`).

## Evidencias desta execucao
- Log local E2E: `docs/futuro/snapshots/e2e_nf/e2e_nf_local_2026-03-14.log`
- Suite ampliada validada: `python manage.py test fiscal_regras nota_fiscal integracao_nfe --keepdb`

## Dependencia operacional externa (GitHub)
- Item pendente: tornar o job E2E obrigatorio na branch principal.
- Status tecnico: pronto no repositorio (`.github/workflows/e2e-nota-fiscal.yml`).
- Acao necessaria: configuracao administrativa no GitHub (Branch protection / Required status checks).

### Como fazer no GitHub
1. Abrir o repositorio no GitHub.
2. Ir em `Settings` -> `Branches`.
3. Em `Branch protection rules`, criar/editar regra para `main`.
4. Habilitar `Require a pull request before merging` (opcional, recomendado).
5. Habilitar `Require status checks to pass before merging`.
6. Em `Status checks that are required`, selecionar:
- `E2E Nota Fiscal / e2e-nota-fiscal`
- `CI Tests / tests`
7. Salvar a regra.

### Resultado esperado apos configuracao
- PR para `main` so pode ser aprovado/mergeado com ambos jobs verdes.
- Falha de E2E ou testes base bloqueia merge automaticamente.
