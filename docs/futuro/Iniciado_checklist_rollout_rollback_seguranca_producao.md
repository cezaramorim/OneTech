# Checklist de Rollout e Rollback - Seguranca Producao

- Data de criacao: 2026-03-13
- Ultima atualizacao: 2026-03-13
- Escopo: ativacao controlada da baseline estrita de seguranca em ambiente de producao

## Objetivo
Aplicar as configuracoes de seguranca em producao com risco controlado, validacao objetiva e caminho de rollback imediato.

## Artefatos envolvidos
- `config/.env.production.example`
- `scripts/seguranca/validar_baseline_producao.ps1`
- `python manage.py auditar_seguranca --strict`

## Fase 0 - Janela e responsaveis
1. [ ] Definir janela de mudanca com equipe tecnica e negocio.
2. [ ] Definir responsavel tecnico pelo go/no-go da mudanca.
3. [ ] Definir canal de comunicacao durante a janela.
4. [ ] Definir criterio de abortar a mudanca (tempo limite e erro critico).

## Fase 1 - Pre-check tecnico
1. [ ] Garantir backup do `config/.env` atual do servidor.
2. [ ] Garantir backup do build/deploy anterior (ultima versao estavel).
3. [ ] Verificar que o host de producao usa HTTPS funcional.
4. [ ] Confirmar `ALLOWED_HOSTS` correto para todos os dominios ativos.
5. [ ] Confirmar acesso admin/superuser para validacao pos-deploy.

Comando recomendado de baseline antes da mudanca:
```powershell
python manage.py auditar_seguranca
```

## Fase 2 - Aplicacao controlada
1. [ ] Aplicar variaveis com base em `config/.env.production.example` no `.env` de producao.
2. [ ] Garantir os valores minimos:
- `DEBUG=False`
- `USE_HTTPS=True`
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `SECURE_SSL_REDIRECT=True`
- `SECURE_HSTS_SECONDS>0`
- `SECURE_HSTS_INCLUDE_SUBDOMAINS=True`
- `SECURE_HSTS_PRELOAD=True`
3. [ ] Reiniciar aplicacao (gunicorn/uwsgi/servico equivalente).

## Fase 3 - Validacao de gate
1. [ ] Executar validacao guiada:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/seguranca/validar_baseline_producao.ps1 -EnvPath <arquivo-env-producao>
```
2. [ ] Confirmar retorno sem erro.
3. [ ] Executar auditoria estrita diretamente:
```powershell
python manage.py auditar_seguranca --strict
```
4. [ ] Registrar evidencias (saida dos comandos + horario + responsavel).

## Fase 4 - Smoke test funcional
1. [ ] Login no painel com usuario admin.
2. [ ] Navegacao de menu principal sem erro 401/403 indevido.
3. [ ] Testar pelo menos uma rota de cada modulo critico:
- `nota_fiscal`
- `fiscal`
- `relatorios`
- `producao`
- `empresas`
4. [ ] Verificar operacao AJAX de listagem/edicao em pelo menos 2 telas.
5. [ ] Verificar que webhook externo continua com resposta esperada (401 sem assinatura valida).

## Fase 5 - Criterio de go/no-go
Go (manter mudanca):
- Auditoria estrita aprovada.
- Sem regressao funcional critica no smoke test.
- Sem pico anormal de erro 403/500 em logs apos deploy.

No-Go (rollback imediato):
- Falha em `auditar_seguranca --strict`.
- Falha de login/sessao em fluxo principal.
- Erro generalizado em rotas criticas ou AJAX.

## Fase 6 - Rollback
1. [ ] Restaurar backup do `.env` anterior.
2. [ ] Restaurar build/deploy estavel anterior (se necessario).
3. [ ] Reiniciar aplicacao.
4. [ ] Executar:
```powershell
python manage.py auditar_seguranca
```
5. [ ] Confirmar recuperacao dos fluxos criticos.
6. [ ] Registrar incidente com causa raiz e plano de nova tentativa.

## Pos-janela
1. [ ] Publicar resumo da mudanca (resultado, horario, responsavel, evidencias).
2. [ ] Se sucesso, marcar pendencia final do plano de seguranca como concluida.
3. [ ] Se rollback, abrir tarefa com correcoes antes de nova janela.
