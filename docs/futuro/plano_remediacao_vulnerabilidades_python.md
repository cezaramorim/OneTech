# Plano Futuro - Remediacao de Vulnerabilidades Python

- Data de criacao: 2026-03-14
- Status: Planejado para execucao
- Escopo: Atualizacao segura de dependencias com vulnerabilidades reportadas pelo pip-audit

## Objetivo
Reduzir risco de seguranca no ambiente Python do projeto, corrigindo vulnerabilidades com menor impacto funcional possivel.

## Contexto atual
- Auditoria de dependencias ativa na Central de Seguranca.
- Relatorio atual aponta vulnerabilidades em pacotes criticos (ex.: django, cryptography, flask).
- A tela ja exibe `fix_versions` para orientar o patch.

## Estrategia de execucao
1. Atualizar em lotes pequenos (1 a 3 pacotes por ciclo).
2. Rodar testes automatizados apos cada lote.
3. Reexecutar `pip-audit` apos cada lote.
4. Avancar somente com baseline verde.

## Ordem recomendada (prioridade)
### Lote 1 - Framework principal
1. django -> versao segura alvo do ramo 5.1.x (ou superior compativel)

### Lote 2 - Criptografia
1. cryptography -> versao de correcao indicada pelo audit

### Lote 3 - Frameworks auxiliares
1. flask -> versao de correcao indicada pelo audit

### Lote 4 - Demais dependencias com CVE
1. atualizar por gravidade e impacto
2. priorizar CVEs de execucao remota, SQL injection e bypass de auth

## Regras tecnicas obrigatorias
1. Nao atualizar tudo de uma vez.
2. Salvar snapshot de `pip freeze` antes de cada lote.
3. Registrar diff de dependencias por lote.
4. Validar migracoes, auth, fiscal e producao apos cada ciclo.
5. Em caso de regressao, rollback imediato para snapshot anterior.

## Procedimento por lote
1. Snapshot antes:
- `pip freeze > docs/futuro/snapshots/requirements_before_<lote>.txt`

2. Atualizacao:
- `python -m pip install --upgrade <pacote(es)>`

3. Validacao tecnica:
- `python manage.py check`
- `python manage.py test control.tests.SecurityCenterTests --keepdb`
- `python manage.py test`

4. Auditoria de seguranca:
- `python -m pip_audit -f json > docs/futuro/snapshots/pip_audit_after_<lote>.json`

5. Registro de resultado:
- quantidade de CVEs antes/depois
- impacto funcional observado
- decisao: avancar ou rollback

## Validacao funcional minima por lote
1. Login/logout e sessao expirada.
2. Central de Seguranca (auditoria normal, strict, matriz, dependencias).
3. Emissao/edicao de nota fiscal.
4. Listas principais migradas (busca, limpar, editar selecionado, excluir selecionados).

## Criterio de pronto
- Vulnerabilidades criticas/altas eliminadas ou justificadas formalmente.
- Testes principais passando.
- Fluxos criticos sem regressao.
- Novo relatorio `pip-audit` anexado ao projeto.

## Riscos e mitigacao
1. Risco: quebra por dependencia transiente.
- Mitigacao: lote pequeno + snapshot + rollback.

2. Risco: incompatibilidade de API entre versoes.
- Mitigacao: manter ramo compativel e atualizar incrementalmente.

3. Risco: falsa sensacao de seguranca por ignorar CVEs duplicadas.
- Mitigacao: consolidar por `id` e por pacote/versao instalada.

## Entregaveis
- Plano de remediacao executado por lotes.
- Historico de snapshots (before/after).
- Relatorio final com CVEs remanescentes e justificativas.

## Inicio recomendado
- Primeiro ciclo: Lote 1 (django)
- Ao concluir e validar, seguir para Lote 2 (cryptography)
