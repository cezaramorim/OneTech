# fiscal_regras - dicionario de campos 10/03/2026

## fiscal_regras.RegraAliquotaICMS
- `ativo`: habilita ou desabilita aplicacao
- `descricao`: descricao funcional da regra
- `ncm_prefixo`: prefixo de 2 a 8 digitos para match por especificidade
- `prefixo_len`: tamanho do prefixo (calculado)
- `tipo_operacao`: `0` entrada, `1` saida
- `modalidade`: `interna` ou `interestadual`
- `uf_origem`: UF de origem (opcional)
- `uf_destino`: UF de destino (opcional)
- `origem_mercadoria`: origem fiscal (0-8, opcional)
- `cst_icms`: CST preferencial da regra
- `csosn_icms`: CSOSN preferencial da regra
- `aliquota_icms`: aliquota principal (%)
- `fcp`: percentual de FCP (%)
- `reducao_base_icms`: reducao de base (%)
- `prioridade`: desempate funcional entre regras
- `vigencia_inicio` e `vigencia_fim`: janela de aplicacao
- `created_by`/`updated_by`: auditoria de manutencao

## nota_fiscal.ItemNotaFiscal (novos campos)
- `regra_icms_aplicada`: FK para regra usada
- `regra_icms_descricao`: snapshot textual
- `aliquota_icms_origem`: `automatica`, `fallback_produto`, `manual`
- `motor_versao`: versao do motor no momento da resolucao
- `dados_contexto_regra`: JSON com contexto da decisao
