# fiscal_regras - operacao 10/03/2026

## Objetivo
Centralizar regras de aliquota ICMS por NCM, UF origem/destino, modalidade e vigencia.

## Rotas
- `/fiscal-regras/` lista
- `/fiscal-regras/cadastrar/` cadastro
- `/fiscal-regras/editar/<id>/` edicao
- `/fiscal-regras/api/resolver-icms/` simulacao
- `/nota-fiscal/api/resolver-aliquota-item/` endpoint usado pela tela de edicao da NF

## Processo recomendado
1. Cadastrar regras com prioridade e vigencia.
2. Confirmar permissao `fiscal_regras.view_regraaliquotaicms` para perfis de consulta.
3. Confirmar permissao `fiscal_regras.add/change/delete_regraaliquotaicms` para perfis de manutencao.
4. Em NF, ao selecionar produto no item, o sistema resolve e grava auditoria.

## Migrations
- App novo: `fiscal_regras/migrations/0001_initial.py`
- Integracao NF: `nota_fiscal/migrations/0005_itemnotafiscal_aliquota_icms_origem_and_more.py`

## Fluxo de fallback
Quando nao existe regra ativa/vigente:
- tenta aliquota do cadastro fiscal do produto
- registra `aliquota_icms_origem = fallback_produto`
- registra contexto do motor para auditoria
