# -*- coding: utf-8 -*-
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.utils import timezone
import logging

from .models import Lote, LoteDiario, ArracoamentoSugerido, ArracoamentoRealizado, LinhaProducao
from .utils import sugerir_para_lote

@login_required
@require_http_methods(["GET"])
@permission_required('producao.view_lote', raise_exception=True)
def api_sugestoes_arracoamento(request):
    """
    Gera e retorna sugestões de arraçoamento para todos os lotes ativos
    para uma data específica, lendo as projeções sem modificá-las.
    """
    logging.info("Iniciando api_sugestoes_arracoamento.")
    try:
        data_str = request.GET.get('data', date.today().isoformat())
        data_alvo = datetime.strptime(data_str, '%Y-%m-%d').date()
        linha_producao_id = request.GET.get('linha_producao_id')
        logging.info(f"Data alvo: {data_alvo}, Linha Produção ID: {linha_producao_id}")
    except (ValueError, TypeError):
        logging.error("Formato de data inválido na requisição.")
        return JsonResponse({'success': False, 'message': 'Formato de data inválido. Use AAAA-MM-DD.'}, status=400)

    erros = []

    # 1. Busca todos os lotes ativos elegíveis para a data alvo.
    lotes_elegibles = Lote.objects.filter(
        ativo=True,
        quantidade_atual__gt=0,
        data_povoamento__lte=data_alvo
    ).select_related('tanque_atual__linha_producao', 'curva_crescimento')
    
    if linha_producao_id:
        lotes_elegibles = lotes_elegibles.filter(tanque_atual__linha_producao_id=linha_producao_id)
    
    sugestoes_qs = ArracoamentoSugerido.objects.none() # Queryset vazio para unir

    with transaction.atomic():
        for lote in lotes_elegibles:
            # Garante que o LoteDiario exista, mas não sobrescreve dados projetados.
            lote_diario, created = LoteDiario.objects.get_or_create(
                lote=lote,
                data_evento=data_alvo,
            )

            # Se o registro foi recém-criado, significa que a projeção não rodou.
            # Isso é um fallback de segurança, mas o ideal é que a projeção já exista.
            if created:
                logging.warning(f"LoteDiario para lote {lote.id} na data {data_alvo} não existia. Criado em tempo de execução.")
                # Preenche com os dados mais básicos possíveis
                lote_diario.quantidade_projetada = lote.quantidade_inicial
                lote_diario.peso_medio_projetado = lote.peso_medio_atual
                lote_diario.biomassa_projetada = (lote.quantidade_inicial * lote.peso_medio_atual) / Decimal('1000')
                lote_diario.save()

            # Gera uma sugestão de arraçoamento baseada no peso real mais recente.
            resultado_sugestao = sugerir_para_lote(lote)
            
            if 'error' not in resultado_sugestao:
                # Garante que a sugestão exista ou seja atualizada se estiver pendente.
                sugestao, created_sug = ArracoamentoSugerido.objects.get_or_create(
                    lote_diario=lote_diario,
                    defaults={
                        'produto_racao': resultado_sugestao['produto_racao'],
                        'quantidade_kg': resultado_sugestao['quantidade_kg'],
                        'status': 'Pendente'
                    }
                )
                if not created_sug and sugestao.status == 'Pendente':
                    sugestao.produto_racao = resultado_sugestao['produto_racao']
                    sugestao.quantidade_kg = resultado_sugestao['quantidade_kg']
                    sugestao.save()
            else:
                erros.append(f"Lote {lote.nome}: {resultado_sugestao['error']}")

        # Coleta todas as sugestões relevantes para a data e filtro de linha
        sugestoes_qs = ArracoamentoSugerido.objects.filter(
            lote_diario__data_evento=data_alvo
        ).select_related(
            'lote_diario__lote',
            'lote_diario__lote__tanque_atual__linha_producao',
            'produto_racao'
        ).prefetch_related('lote_diario__realizacoes')

        if linha_producao_id:
            sugestoes_qs = sugestoes_qs.filter(lote_diario__lote__tanque_atual__linha_producao_id=linha_producao_id)

    # Ordenação final em memória
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
        if s.status == 'Aprovado':
            realizado = s.lote_diario.realizacoes.order_by('-data_realizacao').first()
            if realizado:
                realizado_id = realizado.id
        
        sugestoes_serializadas.append({
            'sugestao_id': s.id,
            'realizado_id': realizado_id,
            'lote_id': s.lote_diario.lote.id,
            'lote_nome': s.lote_diario.lote.nome,
            'tanque_nome': s.lote_diario.lote.tanque_atual.nome if s.lote_diario.lote.tanque_atual else 'N/A',
            'lote_quantidade_atual': f"{s.lote_diario.lote.quantidade_atual:.2f}",
            'lote_peso_medio_atual': f"{s.lote_diario.peso_medio_projetado:.2f}", # Usa o peso projetado para a exibição
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
    Aprova uma ou mais sugestões, calculando o novo peso real e performance,
    e disparando a re-projeção do ciclo de vida.
    """
    try:
        data = json.loads(request.body)
        lancamentos = data.get('lancamentos', [])
        if not lancamentos:
            return JsonResponse({'success': False, 'message': 'Nenhum lançamento selecionado.'}, status=400)

        from .utils import reprojetar_ciclo_de_vida
        from .models import Produto
        from datetime import datetime

        count = 0
        for item in lancamentos:
            sugestao_id = item.get('sugestao_id')
            quantidade_real_racao = Decimal(item.get('quantidade_real'))
            racao_realizada_id = item.get('racao_realizada_id')

            sugestao = ArracoamentoSugerido.objects.select_related('lote_diario__lote', 'produto_racao').get(id=sugestao_id, status='Pendente')
            lote_diario = sugestao.lote_diario

            if lote_diario.quantidade_real is None:
                lote_diario.quantidade_real = lote_diario.lote.quantidade_atual
            if lote_diario.peso_medio_real is None:
                 lote_diario.peso_medio_real = lote_diario.lote.peso_medio_atual

            dia_anterior = lote_diario.data_evento - timedelta(days=1)
            lote_diario_anterior = LoteDiario.objects.filter(lote=lote_diario.lote, data_evento=dia_anterior).first()
            
            peso_medio_real_anterior = lote_diario.lote.peso_medio_inicial
            if lote_diario_anterior and lote_diario_anterior.peso_medio_real is not None:
                peso_medio_real_anterior = lote_diario_anterior.peso_medio_real

            racao_sugerida_kg = lote_diario.racao_sugerida_kg or Decimal('0.0')
            gpd_projetado = lote_diario.gpd_projetado or Decimal('0.0')
            ganho_de_peso_do_dia = Decimal('0.0')

            if racao_sugerida_kg > 0:
                ratio_racao = quantidade_real_racao / racao_sugerida_kg
                ganho_de_peso_do_dia = gpd_projetado * ratio_racao
            
            lote_diario.peso_medio_real = peso_medio_real_anterior + ganho_de_peso_do_dia
            lote_diario.gpd_real = ganho_de_peso_do_dia
            lote_diario.gpt_real = lote_diario.peso_medio_real - lote_diario.lote.peso_medio_inicial

            racao_final = sugestao.produto_racao
            if racao_realizada_id:
                try:
                    racao_final = Produto.objects.get(pk=racao_realizada_id)
                except Produto.DoesNotExist:
                    logging.warning(f"ID de ração real inválido ({racao_realizada_id}) para sugestão {sugestao_id}. Usando ração sugerida.")
            
            ArracoamentoRealizado.objects.create(
                lote_diario=lote_diario,
                produto_racao=racao_final,
                quantidade_kg=quantidade_real_racao,
                data_realizacao=timezone.make_aware(datetime.combine(lote_diario.data_evento, datetime.min.time())),
                usuario_lancamento=request.user
            )

            lote_diario.conversao_alimentar_real = None
            if lote_diario.gpd_real > 0:
                ganho_biomassa_dia_kg = (lote_diario.gpd_real * lote_diario.quantidade_real) / Decimal('1000')
                if ganho_biomassa_dia_kg > 0:
                    lote_diario.conversao_alimentar_real = quantidade_real_racao / ganho_biomassa_dia_kg

            # --- CORREÇÃO: Calcular e salvar a biomassa_real ---
            lote_diario.biomassa_real = (lote_diario.quantidade_real * lote_diario.peso_medio_real) / Decimal('1000')
            lote_diario.racao_realizada = racao_final
            lote_diario.racao_realizada_kg = quantidade_real_racao
            lote_diario.usuario_edicao = request.user
            
            update_fields = [
                'peso_medio_real', 'gpd_real', 'gpt_real', 'conversao_alimentar_real',
                'racao_realizada', 'racao_realizada_kg', 'usuario_edicao', 'quantidade_real', 'biomassa_real'
            ]
            lote_diario.save(update_fields=update_fields)

            sugestao.status = 'Aprovado'
            sugestao.save(update_fields=['status'])

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
@require_http_methods(["DELETE"])
@permission_required('producao.delete_arracoamentorealizado', raise_exception=True)
@transaction.atomic
def api_delete_arracoamento_realizado(request, pk):
    try:
        obj = ArracoamentoRealizado.objects.select_related('lote_diario__lote').get(pk=pk)
        lote_diario = obj.lote_diario
        lote = lote_diario.lote
        data_evento_revertido = lote_diario.data_evento

        # 1. Reverte o status da sugestão para Pendente
        if hasattr(lote_diario, 'sugestao'):
            sugestao = lote_diario.sugestao
            sugestao.status = 'Pendente'
            sugestao.save(update_fields=['status'])

        # 2. Exclui o lançamento realizado
        obj.delete()

        # 3. Limpa os campos _real do LoteDiario
        lote_diario.racao_realizada = None
        lote_diario.racao_realizada_kg = None
        lote_diario.gpd_real = None
        lote_diario.gpt_real = None
        lote_diario.conversao_alimentar_real = None
        lote_diario.peso_medio_real = None
        lote_diario.usuario_edicao = None
        lote_diario.save()

        # 4. Dispara a re-projeção a partir do dia do lançamento excluído
        from .utils import reprojetar_ciclo_de_vida
        reprojetar_ciclo_de_vida(lote, data_evento_revertido)

        return JsonResponse({'success': True, 'message': 'Lançamento excluído e projeção revertida.'})
    except ArracoamentoRealizado.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Lançamento não encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao excluir lançamento: {str(e)}'}, status=500)

@login_required
@require_http_methods(["POST"])
@permission_required('producao.delete_arracoamentorealizado', raise_exception=True)
@transaction.atomic
def api_bulk_delete_arracoamento_realizado(request):
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        if not ids:
            return JsonResponse({'success': False, 'message': 'Nenhum item selecionado para exclusão.'}, status=400)
        
        from .utils import reprojetar_ciclo_de_vida
        from .models import Lote

        lotes_afetados = {}
        realizados_para_excluir = ArracoamentoRealizado.objects.filter(id__in=ids).select_related('lote_diario__lote')

        for obj in realizados_para_excluir:
            lote_diario = obj.lote_diario
            if hasattr(lote_diario, 'sugestao'):
                sugestao = lote_diario.sugestao
                sugestao.status = 'Pendente'
                sugestao.save(update_fields=['status'])

            lote_diario.racao_realizada = None
            lote_diario.racao_realizada_kg = None
            lote_diario.gpd_real = None
            lote_diario.gpt_real = None
            lote_diario.conversao_alimentar_real = None
            lote_diario.peso_medio_real = None
            lote_diario.usuario_edicao = None
            lote_diario.save()

            lote_id = lote_diario.lote.id
            data_evento = lote_diario.data_evento
            if lote_id not in lotes_afetados or data_evento < lotes_afetados[lote_id]:
                lotes_afetados[lote_id] = data_evento

        deleted_count, _ = realizados_para_excluir.delete()

        for lote_id, data_inicio in lotes_afetados.items():
            lote = Lote.objects.get(id=lote_id)
            reprojetar_ciclo_de_vida(lote, data_inicio)

        return JsonResponse({'success': True, 'message': f'{deleted_count} lançamento(s) excluído(s) e projeções revertidas.'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Requisição JSON inválida.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao excluir lançamentos: {str(e)}'}, status=500)

@login_required
@require_http_methods(["POST"])
@permission_required('producao.change_arracoamentorealizado', raise_exception=True)
@transaction.atomic
def api_update_arracoamento_realizado(request, pk):
    try:
        data = json.loads(request.body)
        obj = ArracoamentoRealizado.objects.select_related('lote_diario__lote').get(pk=pk)
        lote_diario = obj.lote_diario

        obj.quantidade_kg = Decimal(str(data.get('quantidade_kg')))
        obj.observacoes = data.get('observacoes', '')
        obj.usuario_edicao = request.user
        obj.save()

        from .utils import reprojetar_ciclo_de_vida
        from datetime import datetime, timedelta

        dia_anterior = lote_diario.data_evento - timedelta(days=1)
        lote_diario_anterior = LoteDiario.objects.filter(lote=lote_diario.lote, data_evento=dia_anterior).first()
        
        peso_medio_real_anterior = lote_diario.lote.peso_medio_inicial
        if lote_diario_anterior and lote_diario_anterior.peso_medio_real is not None:
            peso_medio_real_anterior = lote_diario_anterior.peso_medio_real

        racao_sugerida_kg = lote_diario.racao_sugerida_kg or Decimal('0.0')
        gpd_projetado = lote_diario.gpd_projetado or Decimal('0.0')
        ganho_de_peso_do_dia = Decimal('0.0')

        if racao_sugerida_kg > 0:
            ratio_racao = obj.quantidade_kg / racao_sugerida_kg
            ganho_de_peso_do_dia = gpd_projetado * ratio_racao
        
        lote_diario.peso_medio_real = peso_medio_real_anterior + ganho_de_peso_do_dia
        lote_diario.gpd_real = ganho_de_peso_do_dia
        lote_diario.gpt_real = lote_diario.peso_medio_real - lote_diario.lote.peso_medio_inicial
        lote_diario.racao_realizada_kg = obj.quantidade_kg

        lote_diario.conversao_alimentar_real = None
        if lote_diario.gpd_real > 0:
            if lote_diario.quantidade_real is None: lote_diario.quantidade_real = lote_diario.lote.quantidade_atual
            ganho_biomassa_dia_kg = (lote_diario.gpd_real * lote_diario.quantidade_real) / Decimal('1000')
            if ganho_biomassa_dia_kg > 0:
                lote_diario.conversao_alimentar_real = obj.quantidade_kg / ganho_biomassa_dia_kg

        lote_diario.save()

        reprojetar_ciclo_de_vida(lote_diario.lote, lote_diario.data_evento + timedelta(days=1))

        return JsonResponse({'success': True, 'message': 'Lançamento atualizado e projeção recalculada.'})
    except ArracoamentoRealizado.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Lançamento não encontrado.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Requisição JSON inválida.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao atualizar lançamento: {str(e)}'}, status=500)

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