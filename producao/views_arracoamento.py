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

from .models import Lote, LoteDiario, ArracoamentoSugerido, ArracoamentoRealizado, LinhaProducao, EventoManejo
from .utils import sugerir_para_lote, reprojetar_ciclo_de_vida, _apurar_quantidade_real_no_dia
# Importa as novas funções de cálculo padronizadas
from .utils_uom import calc_biomassa_kg, calc_fcr, g_to_kg, q3


@login_required
@require_http_methods(["GET"])
@permission_required('producao.view_lote', raise_exception=True)
def api_sugestoes_arracoamento(request):
    # ... (código já refatorado, mantido como está)
    logging.info("Iniciando api_sugestoes_arracoamento.")
    try:
        data_str = request.GET.get('data', date.today().isoformat())
        data_alvo = datetime.strptime(data_str, '%Y-%m-%d').date()
        linha_producao_id = request.GET.get('linha_producao_id')
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'message': 'Formato de data inválido. Use AAAA-MM-DD.'}, status=400)

    erros = []
    lotes_elegibles = Lote.objects.filter(
        ativo=True,
        quantidade_atual__gt=0,
        data_povoamento__lte=data_alvo
    ).select_related('tanque_atual__linha_producao', 'curva_crescimento')

    if linha_producao_id:
        lotes_elegibles = lotes_elegibles.filter(tanque_atual__linha_producao_id=linha_producao_id)

    with transaction.atomic():
        for lote in lotes_elegibles:
            lote_diario, created = LoteDiario.objects.get_or_create(
                lote=lote,
                data_evento=data_alvo,
            )

            if created:
                logging.warning(f"LoteDiario para lote {lote.id} na data {data_alvo} não existia. Criado em tempo de execução.")
                lote_diario.quantidade_projetada = lote.quantidade_atual
                lote_diario.peso_medio_projetado = lote.peso_medio_atual
                # --- CÁLCULO PADRONIZADO ---
                lote_diario.biomassa_projetada = q2(calc_biomassa_kg(lote.quantidade_atual, lote.peso_medio_atual))
                lote_diario.save()

            resultado_sugestao = sugerir_para_lote(lote)
            
            if 'error' not in resultado_sugestao:
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

        sugestoes_qs = ArracoamentoSugerido.objects.filter(
            lote_diario__data_evento=data_alvo
        ).select_related(
            'lote_diario__lote',
            'lote_diario__lote__tanque_atual__linha_producao',
            'produto_racao'
        ).prefetch_related('lote_diario__realizacoes')
    
    if linha_producao_id:
        sugestoes_qs = sugestoes_qs.filter(lote_diario__lote__tanque_atual__linha_producao_id=linha_producao_id)

    todas_sugestoes = sorted(list(sugestoes_qs), key=lambda s: (s.lote_diario.lote.tanque_atual.sequencia if s.lote_diario.lote.tanque_atual else 999999))

    sugestoes_serializadas = []
    for s in todas_sugestoes:
        realizado_id = s.lote_diario.realizacoes.order_by('-data_realizacao').first().id if s.status == 'Aprovado' and s.lote_diario.realizacoes.exists() else None
        sugestoes_serializadas.append({
            'sugestao_id': s.id,
            'realizado_id': realizado_id,
            'lote_id': s.lote_diario.lote.id,
            'lote_nome': s.lote_diario.lote.nome,
            'tanque_nome': s.lote_diario.lote.tanque_atual.nome if s.lote_diario.lote.tanque_atual else 'N/A',
            'lote_quantidade_atual': f"{s.lote_diario.lote.quantidade_atual:.2f}",
            'lote_peso_medio_atual': f"{s.lote_diario.peso_medio_projetado:.2f}",
            'lote_linha_producao': s.lote_diario.lote.tanque_atual.linha_producao.nome if s.lote_diario.lote.tanque_atual and s.lote_diario.lote.tanque_atual.linha_producao else 'N/A',
            'lote_sequencia': s.lote_diario.lote.tanque_atual.sequencia if s.lote_diario.lote.tanque_atual else 'N/A',
            'produto_racao_id': s.produto_racao.id if s.produto_racao else None,
            'produto_racao_nome': s.produto_racao.nome if s.produto_racao else 'N/A',
            'quantidade_kg': f"{s.quantidade_kg:.3f}",
            'quantidade_realizada_kg': f"{s.lote_diario.racao_realizada_kg:.3f}" if s.lote_diario.racao_realizada_kg is not None else "",
            'status': s.status,
        })

    # --- NOVA LÓGICA DE VERIFICAÇÃO DE PENDÊNCIAS ---
    # Identifica dias "pulados" (sem aprovação) entre a última aprovação e a data alvo para cada lote.
    all_pending_dates = set()
    for lote in lotes_elegibles:
        last_approval = LoteDiario.objects.filter(
            lote=lote,
            racao_realizada_kg__isnull=False
        ).order_by('-data_evento').first()

        start_check_date = last_approval.data_evento + timedelta(days=1) if last_approval else lote.data_povoamento

        current_date = start_check_date
        while current_date < data_alvo:
            all_pending_dates.add(current_date)
            current_date += timedelta(days=1)

    pending_previous_approval_dates = sorted(list(all_pending_dates))
    formatted_pending_dates = [d.strftime("%d/%m/%Y") for d in pending_previous_approval_dates]

    return JsonResponse({
        'success': True,
        'sugestoes': sugestoes_serializadas,
        'erros': erros,
        'has_pending_previous_approvals': bool(pending_previous_approval_dates),
        'pending_previous_approval_dates': formatted_pending_dates
    })

@login_required
@require_http_methods(["POST"])
@permission_required('producao.change_arracoamentosugerido', raise_exception=True)
def api_aprovar_arracoamento(request):
    # ... (código já refatorado, mantido como está)
    try:
        data = json.loads(request.body)
        sugestao_id = data.get('sugestao_id')
        quantidade_real_kg = q3(data.get('quantidade_real_kg'))
        observacoes = data.get('observacoes', '')

        if quantidade_real_kg <= 0:
            return JsonResponse({'success': False, 'message': 'A quantidade real deve ser um número positivo.'}, status=400)

        with transaction.atomic():
            sugestao = ArracoamentoSugerido.objects.select_related('lote_diario__lote').get(id=sugestao_id)
            lote = Lote.objects.select_for_update().get(pk=sugestao.lote_diario.lote.pk)
            lote_diario = sugestao.lote_diario

            if sugestao.status == 'Aprovado':
                return JsonResponse({'success': False, 'message': 'Esta sugestão já foi aprovada.'}, status=400)

            sugestao.status = 'Aprovado'
            sugestao.save(update_fields=['status'])

            ArracoamentoRealizado.objects.create(
                lote_diario=lote_diario, produto_racao=sugestao.produto_racao,
                quantidade_kg=quantidade_real_kg, data_realizacao=timezone.now(),
                usuario_lancamento=request.user, observacoes=observacoes
            )

            # --- INÍCIO DA LÓGICA DE CÁLCULO DE MÉTRICAS REAIS ---

            # Define a quantidade inicial do dia com base no dia anterior ou no lote
            dia_anterior = lote_diario.data_evento - timedelta(days=1)
            lote_diario_anterior = LoteDiario.objects.filter(lote=lote, data_evento=dia_anterior).first()
            
            quantidade_inicial_dia = lote.quantidade_inicial
            if lote_diario_anterior and lote_diario_anterior.quantidade_real is not None:
                quantidade_inicial_dia = lote_diario_anterior.quantidade_real
            lote_diario.quantidade_inicial = quantidade_inicial_dia

            # Apura a quantidade real do dia (inicial +/- eventos do dia)
            lote_diario.quantidade_real = _apurar_quantidade_real_no_dia(lote_diario)
            
            # Define o peso médio inicial do dia
            peso_medio_inicial_dia = lote.peso_medio_inicial
            if lote_diario_anterior and lote_diario_anterior.peso_medio_real is not None:
                peso_medio_inicial_dia = lote_diario_anterior.peso_medio_real
            lote_diario.peso_medio_inicial = peso_medio_inicial_dia
            
            # Define a biomassa inicial do dia
            biomassa_inicial_dia = calc_biomassa_kg(lote_diario.quantidade_inicial, lote_diario.peso_medio_inicial)
            lote_diario.biomassa_inicial = biomassa_inicial_dia

            # --- NOVA LÓGICA DE FCR REAL (SEM CIRCULARIDADE) ---
            r = (quantidade_real_kg / (lote_diario.racao_sugerida_kg or Decimal('1'))) if (lote_diario.racao_sugerida_kg or 0) > 0 else Decimal('0')
            FCRp = lote_diario.conversao_alimentar_projetada
            Gp   = calc_biomassa_kg(lote_diario.quantidade_real or lote_diario.quantidade_projetada, (lote_diario.gpd_projetado or Decimal('0')))

            if not FCRp or FCRp <= 0:
                FCRp = calc_fcr(lote_diario.racao_sugerida_kg or Decimal('0'), Gp)

            if r >= 1:
                Greal = min(Gp, quantidade_real_kg / FCRp if FCRp and FCRp > 0 else Decimal('0'))
                FCRreal = calc_fcr(quantidade_real_kg, Greal)
            else:
                alpha = Decimal('0.20')  # ajuste por espécie/fase
                FCRreal = FCRp * (Decimal('1') + alpha * (Decimal('1') - r)) if FCRp else Decimal('0')
                Greal   = quantidade_real_kg / FCRreal if FCRreal and FCRreal > 0 else Decimal('0')

            lote_diario.gpd_real = (Greal * 1000) / (lote_diario.quantidade_real or lote_diario.quantidade_projetada or 1)
            lote_diario.biomassa_real = (lote_diario.biomassa_inicial or 0) + Greal
            lote_diario.conversao_alimentar_real = FCRreal
            
            # Lógica funcional preservada para calcular o peso médio real
            lote_diario.peso_medio_real = (lote_diario.peso_medio_inicial or 0) + lote_diario.gpd_real

            # Calcula o GPT Real
            lote_diario.gpt_real = lote_diario.peso_medio_real - lote.peso_medio_inicial
            
            # Atualiza campos do LoteDiario
            lote_diario.racao_realizada = sugestao.produto_racao
            lote_diario.racao_realizada_kg = quantidade_real_kg
            lote_diario.usuario_lancamento = request.user

            lote_diario.save(update_fields=[
                'quantidade_inicial', 'peso_medio_inicial', 'biomassa_inicial',
                'quantidade_real', 'gpd_real', 'peso_medio_real', 'biomassa_real',
                'conversao_alimentar_real', 'gpt_real', 'racao_realizada', 
                'racao_realizada_kg', 'usuario_lancamento'
            ])

            # --- LÓGICA DE ENCADEAMENTO D -> D+1 ---
            proximo_dia = lote_diario.data_evento + timedelta(days=1)
            proximo = LoteDiario.objects.filter(lote=lote, data_evento=proximo_dia).first()
            if proximo:
                base_bio  = lote_diario.biomassa_real if lote_diario.biomassa_real is not None else lote_diario.biomassa_projetada
                base_peso = lote_diario.peso_medio_real if lote_diario.peso_medio_real is not None else lote_diario.peso_medio_projetado
                base_qtd  = lote_diario.quantidade_real if lote_diario.quantidade_real is not None else lote_diario.quantidade_projetada

                proximo.biomassa_inicial    = base_bio
                proximo.peso_medio_inicial  = base_peso
                proximo.quantidade_inicial  = base_qtd
                proximo.save(update_fields=['biomassa_inicial','peso_medio_inicial','quantidade_inicial'])
            reprojetar_ciclo_de_vida(lote, lote_diario.data_evento + timedelta(days=1))

        return JsonResponse({'success': True, 'message': 'Arraçoamento aprovado e registrado com sucesso.'})

    except ArracoamentoSugerido.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Sugestão de arraçoamento não encontrada.'}, status=404)
    except Exception as e:
        logging.exception(f"Erro inesperado ao aprovar arraçoamento: {e}")
        return JsonResponse({'success': False, 'message': f'Erro ao aprovar arraçoamento: {str(e)}'}, status=500)


# --- Funções Restauradas e Refatoradas ---

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

        if hasattr(lote_diario, 'sugestao'):
            sugestao = lote_diario.sugestao
            sugestao.status = 'Pendente'
            sugestao.save(update_fields=['status'])

        obj.delete()

        lote_diario.racao_realizada = None
        lote_diario.racao_realizada_kg = None
        lote_diario.gpd_real = None
        lote_diario.gpt_real = None
        lote_diario.conversao_alimentar_real = None
        lote_diario.peso_medio_real = None
        lote_diario.usuario_edicao = None
        lote_diario.save()

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
        
        lotes_afetados = {}
        realizados_para_excluir = ArracoamentoRealizado.objects.filter(id__in=ids).select_related('lote_diario__lote')

        for obj in realizados_para_excluir:
            lote_diario = obj.lote_diario
            if hasattr(lote_diario, 'sugestao'):
                lote_diario.sugestao.status = 'Pendente'
                lote_diario.sugestao.save(update_fields=['status'])

            lote_diario.racao_realizada = None
            lote_diario.racao_realizada_kg = None
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

        obj.quantidade_kg = q3(data.get('quantidade_kg'))
        obj.observacoes = data.get('observacoes', '')
        obj.usuario_edicao = request.user
        obj.data_edicao = timezone.now()
        obj.save()

        # --- INÍCIO DA LÓGICA DE CÁLCULO DE MÉTRICAS REAIS ---
        lote = lote_diario.lote
        lote_diario.data_edicao = timezone.now()
        lote_diario.usuario_edicao = request.user

        # Define a quantidade inicial do dia com base no dia anterior ou no lote
        dia_anterior = lote_diario.data_evento - timedelta(days=1)
        lote_diario_anterior = LoteDiario.objects.filter(lote=lote, data_evento=dia_anterior).first()
        
        quantidade_inicial_dia = lote.quantidade_inicial
        if lote_diario_anterior and lote_diario_anterior.quantidade_real is not None:
            quantidade_inicial_dia = lote_diario_anterior.quantidade_real
        lote_diario.quantidade_inicial = quantidade_inicial_dia

        # Apura a quantidade real do dia (inicial +/- eventos do dia)
        lote_diario.quantidade_real = _apurar_quantidade_real_no_dia(lote_diario)
        
        # Define o peso médio inicial do dia
        peso_medio_inicial_dia = lote.peso_medio_inicial
        if lote_diario_anterior and lote_diario_anterior.peso_medio_real is not None:
            peso_medio_inicial_dia = lote_diario_anterior.peso_medio_real
        lote_diario.peso_medio_inicial = peso_medio_inicial_dia
        
        # Define a biomassa inicial do dia
        biomassa_inicial_dia = calc_biomassa_kg(lote_diario.quantidade_inicial, lote_diario.peso_medio_inicial)
        lote_diario.biomassa_inicial = biomassa_inicial_dia

        # --- NOVA LÓGICA DE FCR REAL (SEM CIRCULARIDADE) ---
        r = (obj.quantidade_kg / (lote_diario.racao_sugerida_kg or Decimal('1'))) if (lote_diario.racao_sugerida_kg or 0) > 0 else Decimal('0')
        FCRp = lote_diario.conversao_alimentar_projetada
        Gp   = calc_biomassa_kg(lote_diario.quantidade_real or lote_diario.quantidade_projetada, (lote_diario.gpd_projetado or Decimal('0')))

        if not FCRp or FCRp <= 0:
            FCRp = calc_fcr(lote_diario.racao_sugerida_kg or Decimal('0'), Gp)

        if r >= 1:
            Greal = min(Gp, obj.quantidade_kg / FCRp if FCRp and FCRp > 0 else Decimal('0'))
            FCRreal = calc_fcr(obj.quantidade_kg, Greal)
        else:
            alpha = Decimal('0.20')  # ajuste por espécie/fase
            FCRreal = FCRp * (Decimal('1') + alpha * (Decimal('1') - r)) if FCRp else Decimal('0')
            Greal   = obj.quantidade_kg / FCRreal if FCRreal and FCRreal > 0 else Decimal('0')

        lote_diario.gpd_real = (Greal * 1000) / (lote_diario.quantidade_real or lote_diario.quantidade_projetada or 1)
        lote_diario.biomassa_real = (lote_diario.biomassa_inicial or 0) + Greal
        lote_diario.conversao_alimentar_real = FCRreal

        # Lógica funcional preservada para calcular o peso médio real
        lote_diario.peso_medio_real = (lote_diario.peso_medio_inicial or 0) + lote_diario.gpd_real

        # Calcula o GPT Real
        lote_diario.gpt_real = lote_diario.peso_medio_real - lote.peso_medio_inicial
        
        # Atualiza campos do LoteDiario
        lote_diario.racao_realizada_kg = feed_real_kg

        lote_diario.save(update_fields=[
            'data_edicao', 'usuario_edicao',
            'quantidade_inicial', 'peso_medio_inicial', 'biomassa_inicial',
            'quantidade_real', 'gpd_real', 'peso_medio_real', 'biomassa_real',
            'conversao_alimentar_real', 'gpt_real', 'racao_realizada_kg'
        ])

        # --- LÓGICA DE ENCADEAMENTO D -> D+1 ---
        proximo_dia = lote_diario.data_evento + timedelta(days=1)
        proximo = LoteDiario.objects.filter(lote=lote, data_evento=proximo_dia).first()
        if proximo:
            base_bio  = lote_diario.biomassa_real if lote_diario.biomassa_real is not None else lote_diario.biomassa_projetada
            base_peso = lote_diario.peso_medio_real if lote_diario.peso_medio_real is not None else lote_diario.peso_medio_projetado
            base_qtd  = lote_diario.quantidade_real if lote_diario.quantidade_real is not None else lote_diario.quantidade_projetada

            proximo.biomassa_inicial    = base_bio
            proximo.peso_medio_inicial  = base_peso
            proximo.quantidade_inicial  = base_qtd
            proximo.save(update_fields=['biomassa_inicial','peso_medio_inicial','quantidade_inicial'])

        reprojetar_ciclo_de_vida(lote_diario.lote, lote_diario.data_evento + timedelta(days=1))

        return JsonResponse({'success': True, 'message': 'Lançamento atualizado e projeção recalculada.'})
    except ArracoamentoRealizado.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Lançamento não encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao atualizar lançamento: {str(e)}'}, status=500)

@login_required
@require_http_methods(["GET"])
@permission_required('producao.view_arracoamentorealizado', raise_exception=True)
def api_get_arracoamento_realizado(request, pk):
    try:
        obj = ArracoamentoRealizado.objects.get(pk=pk)
        data = {
            'id': obj.id,
            'lote_diario_id': obj.lote_diario.id,
            'lote_nome': obj.lote_diario.lote.nome,
            'produto_racao_id': obj.produto_racao.id if obj.produto_racao else None,
            'produto_racao_nome': obj.produto_racao.nome if obj.produto_racao else 'N/A',
            'quantidade_kg': float(obj.quantidade_kg),
            'data_realizacao': obj.data_realizacao.isoformat(),
            'observacoes': obj.observacoes,
        }
        return JsonResponse({'success': True, 'data': data})
    except ArracoamentoRealizado.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Lançamento não encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao buscar lançamento: {str(e)}'}, status=500)