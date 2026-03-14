# Plano Futuro - Integracao SIEM

- Data de criacao: 2026-03-14
- Status: Planejado
- Escopo: Integracao externa dos eventos da Central de Seguranca com SIEM

## Objetivo
Implantar a integracao do endpoint de eventos de seguranca com plataforma SIEM para deteccao, alerta e resposta a incidentes em escala.

## O que ja existe
- Endpoint SIEM pronto no backend para leitura dos eventos recentes.
- Eventos com campos operacionais: data/hora, tipo, codigo, usuario, rota, metodo, host/ip, tenant, metadata.
- Controle de acesso por usuario autenticado com permissao de administracao da Central.

## Resultado esperado
- Eventos do sistema sendo coletados automaticamente por ferramenta SIEM.
- Regras de alerta para comportamentos suspeitos.
- Dashboards de risco por usuario/tenant/rota.
- Trilha historica para auditoria e compliance.

## Fases de implantacao

### Fase 1 - Preparacao de contrato e governanca
1. Definir SIEM alvo (ex.: Elastic, Splunk, Sentinel).
2. Congelar contrato JSON da API SIEM do projeto.
3. Definir politica de retencao (30d, 90d, 180d) e mascaramento de dados sensiveis.
4. Definir responsaveis (Tecnico, Seguranca, Operacao).

Entregaveis:
- Documento de contrato de eventos.
- Politica de retencao e privacidade.

### Fase 2 - Seguranca de integracao
1. Criar autenticacao dedicada para integrador (service account) com escopo minimo.
2. Restringir acesso por IP allowlist.
3. Aplicar rate limit por credencial/origem.
4. Adicionar assinatura/HMAC opcional para consumo machine-to-machine.
5. Registrar trilha de auditoria de chamadas ao endpoint SIEM.

Entregaveis:
- Conta tecnica SIEM.
- Regras de firewall/reverse proxy.
- Logs de acesso ao endpoint SIEM.

### Fase 3 - Coleta e ingestao
1. Implementar job de coleta no SIEM (polling com janela incremental).
2. Normalizar timezone e formato de data.
3. Mapear campos para schema do SIEM (ECS/CIM equivalente).
4. Tratar deduplicacao e reprocessamento seguro.
5. Configurar monitoramento de falha de ingestao.

Entregaveis:
- Pipeline de ingestao ativo.
- Mapeamento de campos versionado.

### Fase 4 - Deteccao e alertas
1. Criar regras de deteccao:
- burst de AUTHZ_DENIED por IP/usuario/rota
- acessos repetidos a endpoints sensiveis
- aumento abrupto de negacoes por tenant
- atividade anomala fora do horario esperado
2. Definir severidade e roteamento (email/chat/webhook).
3. Criar playbooks de resposta para cada alerta.

Entregaveis:
- Pacote inicial de regras de deteccao.
- Playbooks operacionais.

### Fase 5 - Operacao e melhoria continua
1. Revisao quinzenal de falsos positivos.
2. Ajuste de thresholds por ambiente e perfil de uso.
3. Relatorio mensal de postura de seguranca.
4. Teste de mesa de incidente (tabletop) trimestral.

Entregaveis:
- Rotina operacional formalizada.
- KPIs de deteccao e resposta.

## Requisitos tecnicos para producao
1. HTTPS obrigatorio ponta-a-ponta.
2. Cabecalhos de seguranca ativos.
3. Relogio sincronizado (NTP) no servidor de aplicacao e SIEM.
4. Backups e retencao de logs alinhados com compliance.
5. Limites de pagina/volume definidos para evitar impacto no sistema.

## KPIs sugeridos
- MTTD (tempo medio para detectar).
- MTTR (tempo medio para responder).
- Taxa de falsos positivos.
- Taxa de falha de ingestao.
- Percentual de eventos sem classificacao.

## Riscos e mitigacoes
1. Risco: excesso de alertas (noise).
- Mitigacao: tuning por baseline e severidade.

2. Risco: vazamento de dados sensiveis em metadata.
- Mitigacao: mascaramento e revisao de payload.

3. Risco: indisponibilidade do SIEM afetar operacao.
- Mitigacao: fila/retry e estrategia de degradacao.

4. Risco: consumo excessivo do endpoint.
- Mitigacao: rate limit, janela incremental e cache.

## Checklist de entrada para execucao
- [ ] SIEM alvo definido.
- [ ] Conta tecnica criada.
- [ ] Allowlist de IP aplicada.
- [ ] Rate limit configurado.
- [ ] Contrato de eventos aprovado.
- [ ] Pipeline de ingestao homologado.
- [ ] Regras de alerta publicadas.
- [ ] Playbooks validados.

## Observacao final
Este plano e de implantacao futura. Nao altera o comportamento atual do sistema ate a aprovacao formal do inicio da execucao.
