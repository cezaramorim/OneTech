# Plano Futuro - Integracao SIEM

- Data de criacao: 2026-03-14
- Data de conclusao (escopo de repositorio): 2026-03-14
- Status: Concluido (implementacao no projeto finalizada)
- Escopo: Endpoint SIEM e controles de seguranca para integracao machine-to-machine

## Objetivo
Disponibilizar integracao segura dos eventos da Central de Seguranca para consumo por SIEM externo, com protecoes de acesso, trilha de auditoria e cobertura de testes.

## Entregas concluidas no repositorio
- [x] Endpoint de eventos SIEM ativo: `GET /gerenciamento/seguranca/siem-eventos/`.
- [x] Autorizacao dual:
- superuser em contexto principal.
- token tecnico (`SECURITY_SIEM_TOKEN`) para integracao externa.
- [x] Restricao opcional por allowlist de IP (`SECURITY_SIEM_ALLOW_IPS`).
- [x] Rate limit opcional por origem (`SECURITY_SIEM_RATE_LIMIT_PER_MINUTE`).
- [x] HMAC opcional com anti-replay (`SECURITY_SIEM_REQUIRE_HMAC`, `SECURITY_SIEM_HMAC_SECRET`, `SECURITY_SIEM_HMAC_MAX_SKEW_SECONDS`).
- [x] Telemetria de uso e negacao no trilho de seguranca (`siem_events_export`, `siem_access_denied`).
- [x] Suite de testes automatizados cobrindo:
- acesso superuser.
- acesso por token tecnico.
- negacao por token invalido.
- negacao por HMAC invalido.
- aplicacao de rate limit.

## Contrato tecnico do endpoint
- Metodo: `GET`
- Query params:
- `since_minutes` (1..10080)
- `limit` (1..2000)
- Headers de autenticacao:
- `Authorization: Bearer <token>` ou `X-SIEM-Token: <token>` (quando token configurado)
- HMAC (opcional):
- `X-SIEM-Timestamp: <epoch-seconds>`
- `X-SIEM-Signature: <sha256_hex>` de `"<timestamp>.<request_full_path>"`

## Variaveis de ambiente adicionadas
- `SECURITY_SIEM_TOKEN`
- `SECURITY_SIEM_ALLOW_IPS`
- `SECURITY_SIEM_RATE_LIMIT_PER_MINUTE`
- `SECURITY_SIEM_REQUIRE_HMAC`
- `SECURITY_SIEM_HMAC_SECRET`
- `SECURITY_SIEM_HMAC_MAX_SKEW_SECONDS`

## Evidencias de validacao
- `python manage.py check` -> OK.
- `python manage.py test control.tests.SecurityCenterTests --keepdb` -> OK.

## Pendencias externas (operacao/integracao)
Estas etapas nao dependem de codigo adicional no projeto, e sim de infraestrutura e plataforma SIEM:
- [ ] Definir SIEM alvo (Elastic/Splunk/Sentinel).
- [ ] Provisionar credencial/token tecnico em producao.
- [ ] Aplicar allowlist de IP em proxy/firewall.
- [ ] Configurar job de coleta incremental no SIEM.
- [ ] Publicar regras de alerta e playbooks operacionais.

## Observacao final
O projeto ficou pronto para integracao SIEM com controles de seguranca robustos. A entrada em operacao depende apenas da configuracao externa da plataforma SIEM e da infraestrutura.
