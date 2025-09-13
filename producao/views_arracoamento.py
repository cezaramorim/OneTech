# -*- coding: utf-8 -*-
import json
from datetime import date, datetime
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.utils import timezone

from .models import Lote, LoteDiario, ArracoamentoSugerido, ArracoamentoRealizado, LinhaProducao
from .utils import sugerir_para_lote

@login_required
@require_http_methods(["GET"])
@permission_required('producao.view_lote', raise_exception=True)
def api_sugestoes_arracoamento(request):
    """
    Gera e retorna sugestões de arraçoamento para todos os lotes ativos
    para uma data específica, evitando duplicatas.
    """
    try:
        data_str = request.GET.get('data', date.today().isoformat())
        data_alvo = datetime.strptime(data_str, '%Y-%m-%d').date()
        linha_producao_id = request.GET.get('linha_producao_id')
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'message': 'Formato de data inválido. Use AAAA-MM-DD.'}, status=400)

    erros = []

    # 1. Identifica lotes que já possuem um registro LoteDiario para a data alvo.
    lotes_com_registro_diario_ids = LoteDiario.objects.filter(
        data_evento=data_alvo
    ).values_list('lote_id', flat=True)

    # 2. Busca lotes elegíveis que ainda não têm registro diário.
    lotes_a_processar = Lote.objects.filter(
        ativo=True,
        quantidade_atual__gt=0,
        data_povoamento__lte=data_alvo
    ).exclude(id__in=lotes_com_registro_diario_ids)

    if linha_producao_id:
        lotes_a_processar = lotes_a_processar.filter(tanque_atual__linha_producao_id=linha_producao_id)

    # 3. Cria LoteDiario e ArracoamentoSugerido atomicamente para os novos lotes.
    if lotes_a_processar.exists():
        with transaction.atomic():
            for lote in lotes_a_processar:
                resultado = sugerir_para_lote(lote)
                if 'error' not in resultado:
                    lote_diario = LoteDiario.objects.create(
                        lote=lote,
                        data_evento=data_alvo,
                        quantidade_real=lote.quantidade_atual,
                        peso_medio_real=lote.peso_medio_atual,
                        biomassa_real=lote.biomassa_atual / Decimal('1000')
                    )
                    ArracoamentoSugerido.objects.create(
                        lote_diario=lote_diario,
                        produto_racao=resultado['produto_racao'],
                        quantidade_kg=resultado['quantidade_kg'],
                        status='Pendente'
                    )
                else:
                    erros.append(f"Lote {lote.nome}: {resultado['error']}")

    # 4. Busca todas as sugestões para a data (incluindo as recém-criadas).
    sugestoes_qs = ArracoamentoSugerido.objects.filter(
        lote_diario__data_evento=data_alvo
    ).select_related(
        'lote_diario__lote',
        'lote_diario__lote__tanque_atual__linha_producao',
        'produto_racao'
    ).prefetch_related('lote_diario__realizacoes') # Otimiza a busca pelos realizados

    if linha_producao_id:
        sugestoes_qs = sugestoes_qs.filter(lote_diario__lote__tanque_atual__linha_producao_id=linha_producao_id)

    # Ordenação final
    todas_sugestoes = sorted(
        list(sugestoes_qs),
        key=lambda s: (
            0 if s.status == 'Pendente' else 1,
            s.lote_diario.lote.tanque_atual.linha_producao.nome if s.lote_diario.lote.tanque_atual and s.lote_diario.lote.tanque_atual.linha_producao else '',
            s.lote_diario.lote.tanque_atual.sequencia if s.lote_diario.lote.tanque_atual else 999999
        )
    )

    # Serialização
    sugestoes_serializadas = []
    for s in todas_sugestoes:
        realizado_id = None
        # Se o status é 'Aprovado', tenta encontrar o ID do registro realizado correspondente.
        if s.status == 'Aprovado':
            realizado = s.lote_diario.realizacoes.order_by('-data_realizacao').first()
            if realizado:
                realizado_id = realizado.id
        
        sugestoes_serializadas.append({
            'sugestao_id': s.id,
            'realizado_id': realizado_id, # ID do ArraçoamentoRealizado para o botão de editar
            'lote_id': s.lote_diario.lote.id,
            'lote_nome': s.lote_diario.lote.nome,
            'tanque_nome': s.lote_diario.lote.tanque_atual.nome if s.lote_diario.lote.tanque_atual else 'N/A',
            'lote_quantidade_atual': f"{s.lote_diario.lote.quantidade_atual:.2f}",
            'lote_peso_medio_atual': f"{s.lote_diario.lote.peso_medio_atual:.2f}",
            'lote_linha_producao': s.lote_diario.lote.tanque_atual.linha_producao.nome if s.lote_diario.lote.tanque_atual and s.lote_diario.lote.tanque_atual.linha_producao else 'N/A',
            'lote_sequencia': s.lote_diario.lote.tanque_atual.sequencia if s.lote_diario.lote.tanque_atual else 'N/A',
            'produto_racao_id': s.produto_racao.id if s.produto_racao else None,
            'produto_racao_nome': s.produto_racao.nome if s.produto_racao else 'N/A',
            'quantidade_kg': f"{s.quantidade_kg:.3f}",
            'quantidade_realizada_kg': f"{s.lote_diario.racao_realizada_kg:.3f}" if s.lote_diario.racao_realizada_kg is not None else "",
            'status': s.status,
        })

    return JsonResponse({'success': True, 'sugestoes': sugestoes_serializadas, 'erros': erros})


@login_required
@require_http_methods(["POST"])
@permission_required('producao.add_arracoamentorealizado', raise_exception=True)
@transaction.atomic
def api_aprovar_arracoamento(request):
    """
    Aprova uma ou mais sugestões, criando/atualizando os registros de ArraçoamentoRealizado
    e LoteDiario, e disparando a re-projeção do ciclo de vida.
    """
    try:
        data = json.loads(request.body)
        lancamentos = data.get('lancamentos', [])
        if not lancamentos:
            return JsonResponse({'success': False, 'message': 'Nenhum lançamento selecionado.'}, status=400)

        # Importa aqui para evitar dependência circular no nível do módulo
        from .utils import reprojetar_ciclo_de_vida
        from .models import Produto
        import logging
        from django.utils import timezone
        from datetime import datetime

        count = 0
        for item in lancamentos:
            sugestao_id = item.get('sugestao_id')
            quantidade_real = Decimal(item.get('quantidade_real'))
            racao_realizada_id = item.get('racao_realizada_id') # Novo campo opcional

            sugestao = ArracoamentoSugerido.objects.select_related('lote_diario__lote', 'produto_racao').get(id=sugestao_id, status='Pendente')
            lote_diario = sugestao.lote_diario

            # Determina qual ração foi usada
            racao_final = sugestao.produto_racao
            if racao_realizada_id:
                try:
                    racao_final = Produto.objects.get(pk=racao_realizada_id)
                except Produto.DoesNotExist:
                    # Se o ID for inválido, mantém a ração sugerida e loga um aviso
                    logging.warning(f"ID de ração real inválido ({racao_realizada_id}) fornecido para sugestão {sugestao_id}. Usando ração sugerida.")
            
            # Cria o registro de arraçoamento realizado
            ArracoamentoRealizado.objects.create(
                lote_diario=lote_diario,
                produto_racao=racao_final,
                quantidade_kg=quantidade_real,
                data_realizacao=timezone.make_aware(datetime.combine(lote_diario.data_evento, datetime.min.time())), # CORRIGIDO com timezone
                usuario_lancamento=request.user
            )
            
            # Atualiza o status da sugestão
            sugestao.status = 'Aprovado'
            sugestao.save(update_fields=['status'])
            
            # Atualiza o LoteDiario com os dados reais do dia
            lote_diario.racao_realizada = racao_final
            lote_diario.racao_realizada_kg = quantidade_real
            # TODO: Chamar função para calcular GPD real, GPT real, etc., e salvar no lote_diario
            lote_diario.save(update_fields=['racao_realizada', 'racao_realizada_kg'])

            # Dispara a re-projeção para os dias seguintes
            try:
                reprojetar_ciclo_de_vida(lote_diario.lote, lote_diario.data_evento + timedelta(days=1))
            except Exception as e:
                logging.error(f"Erro ao re-projetar ciclo de vida para o lote {lote_diario.lote.id} após aprovação: {e}")

            count += 1

        return JsonResponse({'success': True, 'message': f'{count} lançamento(s) aprovado(s) com sucesso.'})

    except ArracoamentoSugerido.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Uma ou mais sugestões não foram encontradas ou já foram aprovadas.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Requisição JSON inválida.'}, status=400)
    except Exception as e:
        logging.error(f"Erro inesperado em api_aprovar_arracoamento: {e}")
        return JsonResponse({'success': False, 'message': f'Ocorreu um erro inesperado: {str(e)}'}, status=500)

@login_required
@require_http_methods(["DELETE"]) # Use DELETE method for RESTful API
@permission_required('producao.delete_arracoamentorealizado', raise_exception=True)
def api_delete_arracoamento_realizado(request, pk):
    try:
        obj = ArracoamentoRealizado.objects.get(pk=pk)
        obj.delete()
        return JsonResponse({'success': True, 'message': 'Lançamento excluído com sucesso.'})
    except ArracoamentoRealizado.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Lançamento não encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao excluir lançamento: {str(e)}'}, status=500)

@login_required
@require_http_methods(["POST"]) # Use POST for bulk delete, as DELETE with body is tricky
@permission_required('producao.delete_arracoamentorealizado', raise_exception=True)
@transaction.atomic
def api_bulk_delete_arracoamento_realizado(request):
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        if not ids:
            return JsonResponse({'success': False, 'message': 'Nenhum item selecionado para exclusão.'}, status=400)
        
        deleted_count, _ = ArracoamentoRealizado.objects.filter(id__in=ids).delete()
        return JsonResponse({'success': True, 'message': f'{deleted_count} lançamento(s) excluído(s) com sucesso.'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Requisição JSON inválida.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao excluir lançamentos: {str(e)}'}, status=500)

# Edit API
@login_required
@require_http_methods(["GET"])
@permission_required('producao.view_arracoamentorealizado', raise_exception=True)
def api_get_arracoamento_realizado(request, pk):
    try:
        obj = ArracoamentoRealizado.objects.get(pk=pk)
        # Serialize the object to JSON
        data = {
            'id': obj.id,
            'lote_diario_id': obj.lote_diario.id,
            'lote_nome': obj.lote_diario.lote.nome,
            'produto_racao_id': obj.produto_racao.id if obj.produto_racao else None,
            'produto_racao_nome': obj.produto_racao.nome if obj.produto_racao else 'N/A',
            'quantidade_kg': float(obj.quantidade_kg), # Convert Decimal to float for JSON
            'data_realizacao': obj.data_realizacao.isoformat(),
            'observacoes': obj.observacoes,
        }
        return JsonResponse({'success': True, 'data': data})
    except ArracoamentoRealizado.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Lançamento não encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao buscar lançamento: {str(e)}'}, status=500)

@login_required
@require_http_methods(["POST"])
@permission_required('producao.change_arracoamentorealizado', raise_exception=True)
@transaction.atomic
def api_update_arracoamento_realizado(request, pk):
    try:
        data = json.loads(request.body)
        obj = ArracoamentoRealizado.objects.get(pk=pk)

        # Update fields
        obj.quantidade_kg = Decimal(str(data.get('quantidade_kg'))) # Ensure Decimal conversion
        obj.observacoes = data.get('observacoes', '')
        obj.usuario_edicao = request.user # CORREÇÃO AQUI
        # You might want to update product_racao or data_realizacao here too,
        # but for simplicity, let's stick to quantity and observations for now.

        obj.save()
        return JsonResponse({'success': True, 'message': 'Lançamento atualizado com sucesso.'})
    except ArracoamentoRealizado.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Lançamento não encontrado.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Requisição JSON inválida.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao atualizar lançamento: {str(e)}'}, status=500)
