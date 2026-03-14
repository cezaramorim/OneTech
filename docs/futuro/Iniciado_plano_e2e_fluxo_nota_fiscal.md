# Plano E2E - Fluxo Completo de Nota Fiscal

- Data de criacao: 2026-03-14
- Status: Iniciado
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

## Criterio de pronto
- Suite E2E executando local sem falha.
- Evidencia de execucao (log + screenshots) salva em `docs/futuro/snapshots/e2e_nf/`.
- Execucao automatica no CI com status obrigatorio para aprovacao.
- Checklist abaixo 100% marcado.

## Checklist
- [ ] Estruturar testes E2E (framework e setup).
- [ ] Implementar fluxo de emissao/edicao completo.
- [ ] Implementar fluxo de importacao XML.
- [ ] Implementar cenarios de permissao de override.
- [ ] Implementar cenarios de erro de rede/servidor.
- [ ] Gerar evidencias de execucao.
- [ ] Rodar em ambiente default e tenant.
- [ ] Publicar workflow CI para E2E de Nota Fiscal.
- [ ] Tornar job E2E obrigatorio no branch principal.
