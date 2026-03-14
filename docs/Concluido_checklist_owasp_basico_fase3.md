# Checklist OWASP Basico - Fase 3

- Data de criacao: 2026-03-13
- Ultima atualizacao: 2026-03-13
- Escopo: baseline operacional de seguranca para app interno

## Itens e Status
1. [x] Controle de acesso backend (nao depender apenas de menu).
2. [x] Respostas padronizadas 401/403 para APIs e AJAX.
3. [x] Logs de negacao de autorizacao com trilha minima (usuario/rota/host/tenant).
4. [x] Sessao e cookies com hardening por ambiente (HttpOnly/Secure/SameSite).
5. [x] Headers de seguranca basicos (nosniff, frame options).
6. [x] Webhook externo com assinatura HMAC e anti-replay.
7. [x] Testes automatizados de autorizacao e isolamento por host/tenant.
8. [x] Comandos de auditoria disponiveis:
- `python manage.py auditar_matriz_acesso`
- `python manage.py auditar_seguranca` (matriz + baseline em uma unica execucao)
- `python manage.py validar_baseline_seguranca` (ambiente atual)
- `python manage.py validar_baseline_seguranca --strict` (gate de producao)

## Evidencias Tecnicas
- Matriz de acesso: `common/access_matrix.py`
- Auditoria menu x matriz: `common/management/commands/auditar_matriz_acesso.py`
- Baseline de seguranca: `common/management/commands/validar_baseline_seguranca.py`
- Handler de excecao DRF: `common/api/exception_handler.py`
- Telemetria authz: `common/security_audit.py`
- Plano mestre: `docs/plano_seguranca_permissoes_endpoints.md`