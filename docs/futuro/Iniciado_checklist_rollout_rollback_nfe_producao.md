# Checklist de Rollout e Rollback da Emissao NFe

- Data de criacao: 2026-03-14
- Status: Ativo
- Escopo: deploy controlado dos ajustes de robustez/seguranca da emissao NFe.
- Objetivo: garantir reversao rapida sem perda de operacao em caso de regressao.

## 1) Pre-Deploy (obrigatorio)
1. [ ] Confirmar branch/tag de release e commit alvo.
2. [ ] Registrar hash atual de producao (`git rev-parse HEAD`).
3. [ ] Executar backup do banco antes do deploy.
4. [ ] Confirmar arquivo de ambiente de producao valido e sem placeholders.
5. [ ] Executar validacao de baseline de seguranca:
   - `python manage.py check`
   - `python manage.py test integracao_nfe nota_fiscal --keepdb`
6. [ ] Janela de deploy aprovada com responsavel tecnico e responsavel negocio.

## 2) Deploy
1. [ ] Atualizar codigo para o commit de release.
2. [ ] Aplicar migracoes pendentes:
   - `python manage.py migrate`
3. [ ] Reiniciar servico web e workers.
4. [ ] Rodar smoke test funcional:
   - abrir lista de emissao
   - editar nota de saida
   - tentar emissao de nota invalida (esperado: bloqueio do gate)
   - validar webhook assinado de teste (esperado: 200 quando transicao valida)

## 3) Criterios Go/No-Go
Go (segue operacao):
- Sem erro 5xx novo nas rotas de NF.
- Emissao valida vai para estado `enviada`.
- Webhook atualiza status respeitando transicoes.
- Nenhum bypass de permissao/tenant identificado.

No-Go (rollback imediato):
- Erro 500 recorrente em emissao/edicao/importacao.
- Transicao de status incoerente (ex.: cancelada -> autorizada).
- Bloqueio indevido para usuario autorizado.
- Regressao grave de dados na nota.

## 4) Rollback Tecnico (imediato)
1. [ ] Colocar aplicacao em modo manutencao (ou congelar novas emissoes).
2. [ ] Voltar codigo para hash anterior validado:
   - `git checkout <hash_anterior>`
3. [ ] Se necessario, reverter migracao apenas dos campos novos de pre-emissao:
   - `python manage.py migrate nota_fiscal 0006`
   - Observacao: somente executar se houver incompatibilidade funcional com o schema novo.
4. [ ] Restaurar backup do banco (se houver dano de dados funcional).
5. [ ] Reiniciar servico web e workers.
6. [ ] Reexecutar smoke rapido:
   - login
   - lista emissao
   - edicao NF
   - importacao XML

## 5) Evidencias Minimas
1. [ ] Anexar hash pre e pos deploy.
2. [ ] Registrar horario de inicio/fim da janela.
3. [ ] Salvar resultado dos testes/smokes.
4. [ ] Registrar decisao final: Go ou Rollback.

## 6) Validacao Local desta Rodada (2026-03-14)
- `python manage.py check`: OK
- `python manage.py test integracao_nfe nota_fiscal --keepdb`: OK
- `python manage.py test fiscal_regras nota_fiscal integracao_nfe --keepdb`: OK
- Resultado: apto para homologacao controlada com rollback definido.
