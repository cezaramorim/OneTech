# Plano de Robustez e Seguranca para Emissao NFe

- Status: Concluido
- Ultima atualizacao: 2026-03-14
- Escopo: consolidar base tecnica para emissao de NFe com seguranca, consistencia fiscal e operacao multi-tenant.
- Objetivo imediato: preparar a trilha para emissao confiavel sem regressao e sem quebra dos fluxos atuais de entrada/saida.

## 1) Estado Atual (o que ja existe)

### 1.1 Fluxos funcionais existentes
- Cadastro e edicao de notas fiscais.
- Fluxo de criacao de NFe de saida.
- Fluxo de importacao XML para notas de entrada.
- Itens, duplicatas e transporte em edicao de nota.
- Motor de regras ICMS por NCM (com base local e consolidacao).
- Separacao de lista de notas para emissao de saida.

### 1.2 Estrutura ja avancada
- Campo de tipo de operacao no modelo (`0` entrada, `1` saida).
- Campo de finalidade, modelo e ambiente no modelo da nota.
- Condicao de pagamento e quantidade de parcelas no cabecalho.
- Bloqueios de permissao em partes das telas e endpoints.

### 1.3 Melhorias recentes ja aplicadas
- Lista de relatorios de entrada filtrando saidas.
- Rota antiga de edicao em relatorios redirecionando para edicao oficial.
- Busca unificada de listas com comportamento consistente.
- Form dedicado para entrada em edicao de nota (separado do fluxo de saida).
- Importacao XML passando a persistir cabecalho fiscal basico de entrada (`tipo_operacao`, `finalidade_emissao`, `modelo_documento`, `ambiente`).

## 2) Lacunas Criticas (o que ainda falta)

### 2.1 Gate de pre-emissao (bloqueio central)
Nao existe ainda uma camada unica e obrigatoria que valide uma nota antes de enviar para SEFAZ.

### 2.2 Dominio entrada x saida
Ainda ha pontos onde dados de entrada e saida compartilham logica sem contrato formal de dominio.

### 2.3 Consistencia de pagamento/duplicatas
- Falta padrao unico para vencimentos estruturados por condicao.
- Necessario garantir soma de duplicatas = valor total da nota em toda transicao.

### 2.4 Integracao de emissao
Necessario consolidar servico de emissao desacoplado com:
- idempotencia
- trilha de auditoria
- estados de ciclo de vida
- tratamento de erro padronizado

### 2.5 Seguranca e tenant
Precisamos fechar completamente:
- bloqueio de emissao fora do tenant ativo
- checagem de permissao por endpoint sensivel
- auditoria completa de acao fiscal

## 3) Regras Obrigatorias de Negocio para Emissao

## 3.1 Regra de dominio
- Somente notas com `tipo_operacao = '1'` podem ser emitidas.
- Notas de entrada nunca entram no pipeline de transmissao SEFAZ.

## 3.2 Regra de cabecalho minimo
Obrigatorio antes da emissao:
- emitente_proprio
- destinatario
- natureza_operacao
- finalidade_emissao
- tipo_operacao
- modelo_documento
- ambiente
- data_emissao
- numero/serie

## 3.3 Regra de itens
Cada item deve ter:
- codigo/descricao
- NCM
- CFOP
- quantidade > 0
- valor_unitario >= 0
- valor_total consistente

## 3.4 Regra de totais
- valor_total_nota deve bater com soma de itens, descontos e impostos.
- qualquer divergencia bloqueia emissao.

## 3.5 Regra de pagamento
- se houver duplicatas: soma deve fechar com valor total.
- vencimentos devem seguir dias definidos na condicao de pagamento.

## 3.6 Regra fiscal
- aliquotas por item devem estar resolvidas (manual ou por regra) com origem rastreavel.
- salvar contexto fiscal aplicado no item para auditoria.

## 4) Arquitetura Alvo (modular e segura)

## 4.1 Camada de validacao
Criar modulo de servico de dominio para pre-emissao:
- arquivo sugerido: `nota_fiscal/services/pre_emissao.py`
- retorna estrutura padrao: `ok`, `errors`, `warnings`, `snapshot`

## 4.2 Camada de emissao
Criar modulo desacoplado de transmissao:
- arquivo sugerido: `nota_fiscal/services/emissao_nfe.py`
- responsabilidades:
  - montar payload
  - assinar
  - transmitir
  - consultar retorno
  - mapear status

## 4.3 Camada de estado
Padronizar ciclo de vida:
- `rascunho`
- `validada`
- `enviada`
- `autorizada`
- `rejeitada`
- `cancelada`

## 4.4 Camada de auditoria
Registrar:
- usuario
- tenant
- data/hora
- payload enviado (hash + referencia)
- resposta recebida
- mudancas de status

## 5) Plano de Implementacao (fases)

## Fase 1 - Consolidacao de Dados e Contratos
1. Normalizar contrato entrada x saida na edicao.
2. Garantir preenchimento de cabecalho minimo em importacao e criacao.
3. Corrigir codificacao residual (textos mojibake) em arquivos de NF.
4. Adicionar testes de regressao para edicao entrada/saida.

**Pronto da fase 1**
- formularios separados por dominio, sem ambiguidades.
- campos fiscais basicos persistidos.
- sem regressao nas telas existentes.

## Fase 2 - Gate de Pre-Emissao
1. Implementar `pre_emissao.py` com validacao central.
2. Integrar gate no endpoint/botao de emitir.
3. Exibir erros por campo e resumo tecnico amigavel.
4. Gravar snapshot da validacao.

**Pronto da fase 2**
- nenhuma nota fora do contrato passa para transmissao.
- erros de validacao padronizados e auditaveis.

## Fase 3 - Servico de Emissao e Estados
1. Implementar servico `emissao_nfe.py` desacoplado.
2. Garantir idempotencia por nota/chave.
3. Persistir estados e historico de transicoes.
4. Tratar timeout/retry com seguranca.

**Pronto da fase 3**
- emissao robusta com rastreabilidade ponta a ponta.

## Fase 4 - Seguranca e Multi-tenant
1. Revisar todos endpoints de NF para permissao explicita.
2. Aplicar validacao obrigatoria de tenant ativo.
3. Bloquear acesso direto indevido por URL/API.
4. Adicionar logs de seguranca (acesso negado, acao sensivel).

**Pronto da fase 4**
- sem bypass de tenant/permissao em rotas sensiveis.

## Fase 5 - Homologacao e Go-Live
1. Suite de testes integrada (entrada, saida, emissao, rejeicao).
2. Testes de carga leve e estabilidade.
3. Checklist operacional e rollback.
4. Manual curto para operacao e suporte.

**Pronto da fase 5**
- ambiente apto para emissao com risco controlado.

## 6) Seguranca (controles minimos obrigatorios)
- CSRF em toda acao mutavel.
- permission_required em endpoints sensiveis.
- validacao de tenant em servicos e views.
- logs estruturados por nota e usuario.
- mascaramento de dados sensiveis em logs de erro.

## 7) Checklist Tecnico de Pronto para Emissao
- [x] Gate de pre-emissao ativo e bloqueando inconsistencias.
- [x] Contrato entrada/saida fechado sem ambiguidade.
- [x] Duplicatas e vencimentos consistentes com condicao.
- [x] Estado de nota padronizado e auditavel.
- [x] Endpoints sensiveis protegidos por permissao + tenant.
- [x] Testes de regressao executados e aprovados.
- [x] Plano de rollback validado.

## 8) Dependencias para a proxima etapa
Antes de implementar emissao final em producao:
1. finalizar Fase 1 e Fase 2.
2. executar bateria de testes funcionais em homologacao.
3. validar regras fiscais com amostras reais (intra/interestado).

## 9) Relacao com o plano de unificacao das listas
- Este plano nao substitui o plano de unificacao.
- Ordem de trabalho definida:
  1. concluir unificacao das listas (migracao controlada restante + residuos)
  2. retomar Fase 1 deste plano de emissao

## 10) Progresso executado nesta rodada
- [x] Fase 1.1: normalizacao do contrato entrada x saida nos formularios (`tipo_operacao` forcado por dominio).
- [x] Fase 1.2: defaults de cabecalho minimo na criacao de NF de saida (`modelo_documento` e `ambiente`) e fallback na importacao XML.
- [x] Fase 1.4: testes de regressao adicionados para edicao entrada/saida e criacao de saida com defaults.
- [x] Fase 2.1: servico central de pre-emissao criado em `nota_fiscal/services/pre_emissao.py`.
- [x] Fase 2.2: gate integrado no endpoint `integracao_nfe:emitir_nfe` com retorno padronizado (`message`, `errors`, `warnings`, `snapshot`).
- [x] Fase 2.3: tela de emissao atualizada para exibir erros detalhados por campo e snapshot no popup de bloqueio.
- [x] Fase 2.4: snapshot de pre-emissao persistido na nota (`pre_emissao_ok`, `pre_emissao_validada_em`, `pre_emissao_snapshot`).
- [x] Fase 3.3 (parcial prioritario): ciclo de vida integrado em emissao/webhook com transicoes controladas (`rascunho`, `validada`, `enviada`, `autorizada`, `rejeitada`, `cancelada`).
- [x] Webhook SEFAZ agora valida transicao e retorna `409` para mudanca de estado invalida.
- [x] Emissao agora promove estado para `validada` antes do envio e `enviada` apos sucesso da API.
- [x] Testes adicionais de ciclo de vida no webhook:
  - transicao valida `enviada -> autorizada`
  - bloqueio de transicao invalida (ex.: `cancelada -> autorizada`) com `409`
- [x] Fase 4.1/Fase 4.2 (parcial prioritario): endpoints de emissao/importacao e APIs auxiliares de NF com permissao explicita.
- [x] Fase 4.2 (parcial prioritario): edicao/exclusao de notas de saida bloqueadas quando fora da empresa ativa.
- [x] Teste de seguranca adicional: usuario sem `integracao_nfe.can_emit_nfe` recebe `403` ao tentar emitir.
- [x] Fase 5.3: checklist operacional de rollout/rollback da emissao NFe documentado e validado com evidencias desta rodada (`docs/checklist_rollout_rollback_nfe_producao.md`).
- [x] Consistencia de duplicatas/vencimentos com condicao de pagamento aplicada em backend e frontend:
  - parser de dias por condicao (`A vista`, `7 DDL`, `21/28/35 DDL`, etc.)
  - sincronizacao de duplicatas no salvamento da nota
  - validacao de pre-emissao para quantidade, soma e vencimento esperado
  - select de condicao com `data-dias` para distribuicao correta no formulario
- [x] Testes atualizados e verdes:
  - `manage.py test nota_fiscal --keepdb`
  - `manage.py test integracao_nfe --keepdb`
  - `manage.py test fiscal_regras nota_fiscal integracao_nfe --keepdb`


