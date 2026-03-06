# -*- coding: utf-8 -*-
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.db.models import Sum, Q, F, Value, Case, When, Max
from django.db.models.fields import DecimalField
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction, DatabaseError
from django.utils import timezone
from django.utils.timezone import localdate
import logging

from .models import Lote, LoteDiario, ArracoamentoSugerido, ArracoamentoRealizado, LinhaProducao, EventoManejo, ParametroAmbientalDiario
from .utils import sugerir_racao_para_dia, reprojetar_ciclo_de_vida, _apurar_quantidade_real_no_dia, recalcular_lote_diario_real, obter_base_sugerida, fator_resposta_biologica, calcular_fator_ambiente, obter_tanque_lote_em_data, construir_resolvedor_tanque_lote
from .utils_uom import calc_biomassa_kg, calc_fcr, g_to_kg, q2, q3
from produto.models import Produto

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
@permission_required('producao.view_lote', raise_exception=True)
def api_sugestoes_arracoamento(request):
    logger.info("="*50)
    logger.info("Iniciando api_sugestoes_arracoamento")
    
    try:
        logger.info(f"GET params: {dict(request.GET)}")
        
        data_inicial_str = request.GET.get('data_inicial')
        data_final_str = request.GET.get('data_final')
        
        if not data_inicial_str or not data_final_str:
            logger.warning("Parâmetros data_inicial e data_final são obrigatórios")
            return JsonResponse({
                'success': False, 
                'message': 'Parâmetros data_inicial e data_final são obrigatórios.'
            }, status=400)
            
        data_inicial = datetime.strptime(data_inicial_str, '%Y-%m-%d').date()
        data_final = datetime.strptime(data_final_str, '%Y-%m-%d').date()
        
        linha_producao_id = request.GET.get('linha_producao_id')
        # CORREÇÃO: valor padrão vazio para status
        status_filtro = request.GET.get('status', '')
        logger.info(f"linha_producao_id: {linha_producao_id}, status_filtro: '{status_filtro}'")
        
    except (ValueError, TypeError) as e:
        logger.error(f"Erro ao converter datas: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': f'Formato de data inválido. Use AAAA-MM-DD. Erro: {str(e)}'
        }, status=400)

    erros = []
    
    # Busca todos os lotes ativos
    lotes_query = Lote.objects.filter(
        ativo=True,
        data_povoamento__lte=data_final
    ).select_related(
        'tanque_atual__linha_producao', 
        'curva_crescimento',
        'fase_producao'
    )

    if linha_producao_id:
        lotes_query = lotes_query.filter(tanque_atual__linha_producao_id=linha_producao_id)

    # Filtra lotes com quantidade > 0
    lotes_com_estoque = []
    for lote in lotes_query:
        try:
            entradas = EventoManejo.objects.filter(
                lote=lote,
                data_evento__lte=data_final
            ).filter(
                Q(tipo_evento__nome='Povoamento') | Q(tipo_movimento='Entrada')
            ).aggregate(total=Sum('quantidade'))['total'] or 0
            
            saidas = EventoManejo.objects.filter(
                lote=lote,
                data_evento__lte=data_final
            ).filter(
                Q(tipo_evento__nome__in=['Mortalidade', 'Despesca']) | Q(tipo_movimento='Saída')
            ).aggregate(total=Sum('quantidade'))['total'] or 0
            
            quantidade_atual = entradas - saidas
            
            if quantidade_atual > 0:
                lote.quantidade_atual_calculada = quantidade_atual
                lotes_com_estoque.append(lote)
                
        except Exception as e:
            logger.error(f"Erro ao calcular quantidade para lote {lote.id}: {str(e)}")
            erros.append(f"Erro ao processar lote {lote.nome}: {str(e)}")

    # Processa cada lote
    with transaction.atomic():
        for lote in lotes_com_estoque:
            try:
                data_inicio_lote = data_inicial
                if lote.data_povoamento:
                    data_inicio_lote = max(data_inicial, lote.data_povoamento)

                # Não cria histórico para período anterior ao povoamento do lote.
                if data_inicio_lote > data_final:
                    continue

                tanque_resolver = construir_resolvedor_tanque_lote(lote)
                lotes_diarios = LoteDiario.objects.filter(
                    lote=lote,
                    data_evento__gte=data_inicio_lote,
                    data_evento__lte=data_final
                ).order_by('data_evento')

                for lote_diario in lotes_diarios:
                    data_atual = lote_diario.data_evento
                    tanque_snapshot = tanque_resolver(data_atual)
                    tanque_snapshot_id = tanque_snapshot.id if tanque_snapshot else None
                    if lote_diario.tanque_id != tanque_snapshot_id:
                        lote_diario.tanque = tanque_snapshot
                        lote_diario.save(update_fields=['tanque'])

                    # CORREÇÃO: gera sugestão apenas se o filtro for adequado (evita gerar para 'Aprovado')
                    if status_filtro in ['', 'Todos', 'Pendente']:
                        sugestao_existente = ArracoamentoSugerido.objects.filter(
                            lote_diario=lote_diario
                        ).first()

                        if sugestao_existente and sugestao_existente.status == 'Aprovado':
                            continue

                        try:
                            resultado_sugestao = sugerir_racao_para_dia(lote_diario)
                        except Exception as e:
                            logger.error(f"Erro ao gerar sugestão: {str(e)}")
                            erros.append(f"Lote {lote.nome} data {data_atual}: Erro ao gerar sugestão - {str(e)}")
                            continue

                        if 'error' not in resultado_sugestao:
                            try:
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
                            except Exception as e:
                                logger.error(f"Erro ao salvar sugestão: {str(e)}")
                                erros.append(f"Lote {lote.nome} data {data_atual}: Erro ao salvar sugestão - {str(e)}")
                        else:
                            erros.append(f"Lote {lote.nome} data {data_atual}: {resultado_sugestao['error']}")
                    
            except Exception as e:
                erro_msg = f"Lote {lote.nome}: {str(e)}"
                logger.error(erro_msg, exc_info=True)
                erros.append(erro_msg)
                if len(erros) > 10:
                    erros.append("Muitos erros encontrados. Processamento interrompido.")
                    break

        # Busca as sugestões para o período
        try:
            sugestoes_qs = ArracoamentoSugerido.objects.filter(
                lote_diario__data_evento__gte=data_inicial,
                lote_diario__data_evento__lte=data_final
            ).select_related(
                'lote_diario__lote',
                'lote_diario__tanque__linha_producao',
                'lote_diario__lote__tanque_atual__linha_producao',
                'lote_diario__lote__fase_producao',
                'produto_racao'
            ).prefetch_related('lote_diario__realizacoes')

            if linha_producao_id:
                sugestoes_qs = sugestoes_qs.filter(
                    Q(lote_diario__tanque__linha_producao_id=linha_producao_id) |
                    Q(lote_diario__tanque__isnull=True, lote_diario__lote__tanque_atual__linha_producao_id=linha_producao_id)
                )

            # CORREÇÃO: se status_filtro for vazio ou 'Todos', não filtra por status
            if status_filtro and status_filtro != 'Todos':
                sugestoes_qs = sugestoes_qs.filter(status=status_filtro)

        except Exception as e:
            logger.error(f"Erro ao buscar sugestões: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': f'Erro ao buscar sugestões: {str(e)}'
            }, status=500)

    # Ordena as sugestões
    todas_sugestoes = sorted(
        list(sugestoes_qs), 
        key=lambda s: (
            s.lote_diario.data_evento,
            s.lote_diario.tanque.sequencia if s.lote_diario.tanque else (s.lote_diario.lote.tanque_atual.sequencia if s.lote_diario.lote.tanque_atual else 999999)
        )
    )

    # --- Ambiente por Fase ---
    fase_ids = set()
    for s in todas_sugestoes:
        if s.lote_diario.lote.fase_producao:
            fase_ids.add(s.lote_diario.lote.fase_producao.id)

    ambiente_por_fase = {}
    if fase_ids:
        datas = set(s.lote_diario.data_evento for s in todas_sugestoes)
        for data in datas:
            try:
                qs_amb = ParametroAmbientalDiario.objects.filter(
                    data=data,
                    fase_id__in=list(fase_ids)
                )
                for amb in qs_amb:
                    ambiente_por_fase[(amb.fase_id, data)] = amb
            except Exception as e:
                logger.error(f"Erro ao buscar ambiente para data {data}: {str(e)}")

    
    # --- Verificação de pendências anteriores à data inicial ---
        # --- Verificação de pendências anteriores à data inicial ---
    logger.info("Verificando pendências anteriores à data inicial...")
    lotes_com_pendencias = []
    for lote in lotes_com_estoque:
        try:
            # ?ltima data realizada antes da data inicial (baseada no evento realizado)
            data_ultimo = ArracoamentoRealizado.objects.filter(
                lote_diario__lote=lote,
                data_evento__lt=data_inicial
            ).aggregate(max_data=Max('data_evento'))['max_data']
            
            if data_ultimo:
                data_inicio_pendencia = max(data_ultimo + timedelta(days=1), lote.data_povoamento)
                # Pend?ncia ? calculada por data:
                # existe LoteDiario no intervalo cuja data n?o aparece em nenhuma realiza??o.
                datas_realizadas_no_intervalo = ArracoamentoRealizado.objects.filter(
                    lote_diario__lote=lote,
                    data_evento__gte=data_inicio_pendencia,
                    data_evento__lt=data_inicial
                ).values('data_evento')

                dias_sem_aprovacao = LoteDiario.objects.filter(
                    lote=lote,
                    data_evento__gte=data_inicio_pendencia,
                    data_evento__lt=data_inicial
                ).exclude(
                    data_evento__in=datas_realizadas_no_intervalo
                ).exists()
                if dias_sem_aprovacao:
                    lotes_com_pendencias.append({
                        'lote_nome': lote.nome,
                        'ultima_data': data_ultimo.strftime("%d/%m/%Y")
                    })
            else:
                # Nunca houve realiza??o antes da data inicial
                data_inicio_pendencia = lote.data_povoamento
                datas_realizadas_no_intervalo = ArracoamentoRealizado.objects.filter(
                    lote_diario__lote=lote,
                    data_evento__gte=data_inicio_pendencia,
                    data_evento__lt=data_inicial
                ).values('data_evento')
                dias_sem_aprovacao = LoteDiario.objects.filter(
                    lote=lote,
                    data_evento__gte=data_inicio_pendencia,
                    data_evento__lt=data_inicial
                ).exclude(
                    data_evento__in=datas_realizadas_no_intervalo
                ).exists()
                if dias_sem_aprovacao:
                    lotes_com_pendencias.append({
                        'lote_nome': lote.nome,
                        'ultima_data': 'Nunca aprovado'
                    })
        except Exception as e:
            logger.error(f"Erro ao verificar pend?ncias para lote {lote.id}: {str(e)}")
        except Exception as e:
            logger.error(f"Erro ao verificar pendências para lote {lote.id}: {str(e)}")
    # Serializa as sugestões
    sugestoes_serializadas = []
    totais = {
        'total_sugerido_kg': Decimal('0'),
        'total_real_kg': Decimal('0')
    }

    for s in todas_sugestoes:
        try:
            realizado = s.lote_diario.realizacoes.first()
            realizado_id = realizado.id if realizado else None
            racao_realizada_obj = s.lote_diario.racao_realizada
            tanque_no_dia = s.lote_diario.tanque or s.lote_diario.lote.tanque_atual

            fase = s.lote_diario.lote.fase_producao
            data = s.lote_diario.data_evento
            param_amb = ambiente_por_fase.get((fase.id, data)) if fase else None
            
            if param_amb:
                amb = calcular_fator_ambiente(param_amb)
            else:
                amb = {'fator_ambiente': Decimal('1.00'), 'od_medio': None, 'temp_media': None, 'variacao_termica': None}

            fator_manejo = Decimal('1.00')

            qtd_sugerida = Decimal(s.quantidade_kg or 0)
            qtd_ajustada = (qtd_sugerida * amb['fator_ambiente'] * fator_manejo) if qtd_sugerida > 0 else Decimal('0')

            totais['total_sugerido_kg'] += qtd_sugerida
            if realizado:
                totais['total_real_kg'] += realizado.quantidade_kg

            sugestoes_serializadas.append({
                'id': s.id,
                'lote_diario_id': s.lote_diario.id,
                'realizado_id': realizado_id,
                'data': data.strftime("%d/%m/%Y"),
                'data_iso': data.isoformat(),
                'lote_id': s.lote_diario.lote.id,
                'lote_nome': s.lote_diario.lote.nome,
                'tanque_nome': tanque_no_dia.nome if tanque_no_dia else 'N/A',
                'fase_id': s.lote_diario.lote.fase_producao.id if s.lote_diario.lote.fase_producao else None,
                'fase_nome': s.lote_diario.lote.fase_producao.nome if s.lote_diario.lote.fase_producao else 'N/A',
                'linha_producao_nome': tanque_no_dia.linha_producao.nome if tanque_no_dia and tanque_no_dia.linha_producao else 'N/A',
                'sequencia': tanque_no_dia.sequencia if tanque_no_dia else 'N/A',
                'qtd_lote': f"{s.lote_diario.quantidade_inicial:.0f}" if s.lote_diario.quantidade_inicial is not None else "0",
                'peso_medio': f"{s.lote_diario.peso_medio_inicial:.2f}" if s.lote_diario.peso_medio_inicial is not None else "0.00",
                'racao_sugerida_nome': s.produto_racao.nome if s.produto_racao else 'N/A',
                'racao_realizada_nome': racao_realizada_obj.nome if racao_realizada_obj else 'N/A',
                'qtd_sugerida_kg': f"{qtd_sugerida:.3f}",
                'qtd_sugerida_ajustada_kg': f"{qtd_ajustada:.3f}",
                'qtd_real_kg': f"{realizado.quantidade_kg:.3f}" if realizado else "",
                'status': s.status,
                'fator_ambiente': f"{amb['fator_ambiente']:.2f}" if amb.get('fator_ambiente') else None,
                'od_medio': f"{amb['od_medio']:.2f}" if amb.get('od_medio') else None,
                'temp_media': f"{amb['temp_media']:.2f}" if amb.get('temp_media') else None,
            })
            
        except Exception as e:
            logger.error(f"Erro ao serializar sugestão {s.id}: {str(e)}", exc_info=True)
            erros.append(f"Erro ao processar sugestão {s.id}: {str(e)}")

    return JsonResponse({
        'success': True,
        'sugestoes': sugestoes_serializadas,
        'totais': {
            'total_sugerido_kg': f"{totais['total_sugerido_kg']:.3f}",
            'total_real_kg': f"{totais['total_real_kg']:.3f}"
        },
        'erros': erros,
        'has_pending_previous_approvals': bool(lotes_com_pendencias),
        'pending_previous_approvals': lotes_com_pendencias
    })


@login_required
@require_http_methods(["POST"])
@permission_required(['producao.change_arracoamentosugerido', 'producao.add_arracoamentorealizado'], raise_exception=True)
def api_aprovar_arracoamento(request):
    try:
        data = json.loads(request.body)
        sugestao_id = data.get('sugestao_id')
        lote_diario_id = data.get('lote_diario_id')
        racao_realizada_id = data.get('racao_realizada_id')
        observacoes = data.get('observacoes', '')

        with transaction.atomic():
            sugestao = ArracoamentoSugerido.objects.select_related(
                'lote_diario__lote',
                'produto_racao'
            ).filter(id=sugestao_id).first()

            if not sugestao and lote_diario_id:
                ld = LoteDiario.objects.filter(id=lote_diario_id).first()
                if ld:
                    if ld.realizacoes.exists():
                        return JsonResponse({
                            'success': True,
                            'message': 'Lançamento já aprovado anteriormente.'
                        })
                    sugestao = ArracoamentoSugerido.objects.select_related(
                        'lote_diario__lote',
                        'produto_racao'
                    ).filter(lote_diario=ld).order_by('-id').first()

            if not sugestao:
                return JsonResponse({
                    'success': False,
                    'message': 'Sugestão de arraçoamento não encontrada.'
                }, status=404)
            
            # Verificar se o lote ainda está ativo
            if not sugestao.lote_diario.lote.ativo:
                return JsonResponse({
                    'success': False, 
                    'message': 'Este lote não está mais ativo.'
                }, status=400)
            
            if sugestao.status == 'Aprovado':
                return JsonResponse({
                    'success': True,
                    'message': 'Sugestão já aprovada anteriormente.'
                })

            # Lógica para determinar a quantidade a ser usada
            quantidade_real_kg_str = data.get('quantidade_real_kg')
            quantidade_a_usar = None

            if quantidade_real_kg_str and str(quantidade_real_kg_str).strip():
                try:
                    valor_decimal = Decimal(quantidade_real_kg_str)
                    if valor_decimal > 0:
                        quantidade_a_usar = q3(valor_decimal)
                except (ValueError, TypeError, ArithmeticError):
                    logger.warning(f"Valor inválido para quantidade_real_kg: {quantidade_real_kg_str}")
                    pass

            if quantidade_a_usar is None:
                # Fallback padr?o: usa exatamente a quantidade da sugest?o aprovada na linha.
                quantidade_a_usar = sugestao.quantidade_kg

            if quantidade_a_usar is not None:
                quantidade_a_usar = q3(quantidade_a_usar)

            # Validação final
            if not quantidade_a_usar or quantidade_a_usar <= 0:
                return JsonResponse({
                    'success': False, 
                    'message': 'A quantidade real ou sugerida deve ser um número positivo.'
                }, status=400)

            # Determina qual ração usar: a escolhida pelo usuário ou a sugerida como padrão
            racao_a_ser_usada = sugestao.produto_racao
            if racao_realizada_id:
                try:
                    racao_a_ser_usada = Produto.objects.get(pk=racao_realizada_id)
                except Produto.DoesNotExist:
                    return JsonResponse({
                        'success': False, 
                        'message': f'A ração escolhida com ID {racao_realizada_id} não foi encontrada.'
                    }, status=404)

            # Verificar estoque disponível
            try:
                # Usar select_for_update para bloquear a linha durante a transação
                produto = Produto.objects.select_for_update().get(pk=racao_a_ser_usada.pk)
                
                # Verificar se o produto tem controle de estoque
                if hasattr(produto, 'quantidade_estoque') and produto.quantidade_estoque < quantidade_a_usar:
                    return JsonResponse({
                        'success': False, 
                        'message': f'Estoque insuficiente. Disponível: {produto.quantidade_estoque:.3f} kg'
                    }, status=400)
            except Produto.DoesNotExist:
                return JsonResponse({
                    'success': False, 
                    'message': 'Produto não encontrado durante verificação de estoque.'
                }, status=404)

            # Atualizar status da sugestão
            sugestao.status = 'Aprovado'
            sugestao.save(update_fields=['status'])

            # Criar registro de arraçoamento realizado
            ArracoamentoRealizado.objects.create(
                lote_diario=sugestao.lote_diario,
                data_evento=sugestao.lote_diario.data_evento,
                produto_racao=racao_a_ser_usada,
                quantidade_kg=quantidade_a_usar,
                data_realizacao=timezone.now(),
                usuario_lancamento=request.user,
                observacoes=observacoes
            )

            # --- Lógica de Decréscimo de Estoque ---
            try:
                # Atualizar apenas as saídas (assumindo que quantidade_estoque é calculada)
                Produto.objects.filter(pk=racao_a_ser_usada.pk).update(
                    quantidade_saidas=F('quantidade_saidas') + quantidade_a_usar
                )
                logger.info(f"Estoque do produto '{racao_a_ser_usada.nome}' atualizado. Saídas incrementadas em {quantidade_a_usar} kg.")
            except DatabaseError as e:
                logger.error(f"Erro ao atualizar estoque do produto {racao_a_ser_usada.id}: {e}")
                raise Exception(f"Falha ao atualizar estoque da ração. Operação cancelada.")

            # Atualizar LoteDiario
            lote = sugestao.lote_diario.lote
            lote_diario = sugestao.lote_diario
            ld = lote_diario

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

            lote_diario.racao_realizada = racao_a_ser_usada

            lote_diario.save(update_fields=[
                'quantidade_inicial',
                'quantidade_real',
                'peso_medio_inicial',
                'biomassa_inicial',
                'racao_realizada',
            ])

            # Recalcular métricas do dia
            recalcular_lote_diario_real(ld, request.user)

            # Atualizar o próximo dia
            proximo_dia = lote_diario.data_evento + timedelta(days=1)
            proximo = LoteDiario.objects.filter(lote=lote, data_evento=proximo_dia).first()
            if proximo:
                proximo.biomassa_inicial = ld.biomassa_real if ld.biomassa_real is not None else ld.biomassa_projetada
                proximo.peso_medio_inicial = ld.peso_medio_real if ld.peso_medio_real is not None else ld.peso_medio_projetado
                proximo.quantidade_inicial = ld.quantidade_real if ld.quantidade_real is not None else ld.quantidade_projetada
                proximo.save(update_fields=['biomassa_inicial', 'peso_medio_inicial', 'quantidade_inicial'])

            # Reprojetar ciclo de vida
            reprojetar_ciclo_de_vida(lote, lote_diario.data_evento + timedelta(days=1))

        return JsonResponse({
            'success': True, 
            'message': 'Arraçoamento aprovado e registrado com sucesso.'
        })

    except ArracoamentoSugerido.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Sugestão de arraçoamento não encontrada.'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'message': 'Formato JSON inválido.'
        }, status=400)
    except Exception as e:
        logger.exception(f"Erro inesperado ao aprovar arraçoamento: {e}")
        return JsonResponse({
            'success': False, 
            'message': f'Erro ao aprovar arraçoamento: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["DELETE"])
@permission_required('producao.delete_arracoamentorealizado', raise_exception=True)
@transaction.atomic
def api_delete_arracoamento_realizado(request, pk):
    try:
        obj = ArracoamentoRealizado.objects.select_related(
            'lote_diario__lote',
            'produto_racao'
        ).get(pk=pk)
        
        lote_diario = obj.lote_diario
        lote = lote_diario.lote
        data_evento_revertido = lote_diario.data_evento
        quantidade_devolver = obj.quantidade_kg
        produto = obj.produto_racao

        # Reverter estoque
        if produto and quantidade_devolver:
            try:
                Produto.objects.filter(pk=produto.pk).update(
                    quantidade_saidas=F('quantidade_saidas') - quantidade_devolver
                )
                logger.info(f"Estoque do produto '{produto.nome}' revertido. Saídas decrementadas em {quantidade_devolver} kg.")
            except DatabaseError as e:
                logger.error(f"Erro ao reverter estoque: {e}")
                # Continuar mesmo com erro no estoque Decidir baseado na regra de negócio

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
        lote_diario.data_edicao = timezone.now()
        lote_diario.save()

        reprojetar_ciclo_de_vida(lote, data_evento_revertido)

        return JsonResponse({
            'success': True, 
            'message': 'Lançamento excluído, estoque revertido e projeção recalculada.'
        })
    except ArracoamentoRealizado.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Lançamento não encontrado.'
        }, status=404)
    except Exception as e:
        logger.exception(f"Erro ao excluir lançamento {pk}: {e}")
        return JsonResponse({
            'success': False, 
            'message': f'Erro ao excluir lançamento: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
@permission_required('producao.delete_arracoamentorealizado', raise_exception=True)
@transaction.atomic
def api_bulk_delete_arracoamento_realizado(request):
    try:
        data = json.loads(request.body)
        ids_recebidos = data.get('ids', [])
        if not ids_recebidos:
            return JsonResponse({
                'success': False, 
                'message': 'Nenhum item selecionado para exclusao.'
            }, status=400)

        ids_validos = []
        ids_invalidos = []
        for raw_id in ids_recebidos:
            try:
                item_id = int(raw_id)
                if item_id > 0:
                    ids_validos.append(item_id)
                else:
                    ids_invalidos.append(raw_id)
            except (TypeError, ValueError):
                ids_invalidos.append(raw_id)

        if not ids_validos:
            return JsonResponse({
                'success': False,
                'message': 'Nenhum ID valido foi enviado para exclusao.',
                'invalid_ids': ids_invalidos
            }, status=400)

        if len(ids_validos) > 100:  # Limite de seguran�a
            return JsonResponse({
                'success': False, 
                'message': 'Maximo de 100 itens por operacao em lote.'
            }, status=400)
        
        lotes_afetados = {}
        erros = []
        
        realizados_para_excluir = ArracoamentoRealizado.objects.filter(
            id__in=ids_validos
        ).select_related(
            'lote_diario__lote',
            'produto_racao'
        )

        ids_encontrados = set(realizados_para_excluir.values_list('id', flat=True))
        ids_nao_encontrados = sorted(set(ids_validos) - ids_encontrados)

        if not ids_encontrados:
            return JsonResponse({
                'success': False,
                'message': 'Nenhum lancamento realizado encontrado para os IDs enviados.',
                'missing_ids': ids_nao_encontrados,
                'invalid_ids': ids_invalidos
            }, status=404)

        if ids_nao_encontrados:
            erros.append(f'Lote/tanque sem lancamento aprovado para exclusao (itens: {ids_nao_encontrados})')

        if ids_invalidos:
            erros.append(f'IDs invalidos ignorados: {ids_invalidos}')

        for obj in realizados_para_excluir:
            try:
                lote_diario = obj.lote_diario
                
                # Reverter estoque
                if obj.produto_racao and obj.quantidade_kg:
                    Produto.objects.filter(pk=obj.produto_racao.pk).update(
                        quantidade_saidas=F('quantidade_saidas') - obj.quantidade_kg
                    )

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
                    
            except Exception as e:
                erros.append(f"Erro ao processar item {obj.id}: {str(e)}")

        deleted_count, _ = realizados_para_excluir.delete()

        # Reprojetar ciclos afetados
        for lote_id, data_inicio in lotes_afetados.items():
            try:
                lote = Lote.objects.get(id=lote_id)
                reprojetar_ciclo_de_vida(lote, data_inicio)
            except Lote.DoesNotExist:
                erros.append(f"Lote {lote_id} não encontrado para reprojeção")
            except Exception as e:
                erros.append(f"Erro ao reprojetar lote {lote_id}: {str(e)}")

        mensagem = f'{deleted_count} lancamento(s) excluido(s)'
        if erros:
            mensagem += f' com {len(erros)} erro(s)'

        return JsonResponse({
            'success': True, 
            'message': mensagem,
            'errors': erros if erros else None
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'message': 'Requisicao JSON invalida.'
        }, status=400)
    except Exception as e:
        logger.exception(f"Erro ao excluir lancamentos em lote: {e}")
        return JsonResponse({
            'success': False, 
            'message': f'Erro ao excluir lancamentos: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
@permission_required('producao.change_arracoamentorealizado', raise_exception=True)
@transaction.atomic
def api_update_arracoamento_realizado(request, pk):
    try:
        data = json.loads(request.body)
        obj = ArracoamentoRealizado.objects.select_related(
            'lote_diario__lote',
            'produto_racao'
        ).get(pk=pk)
        
        lote_diario = obj.lote_diario
        quantidade_anterior = obj.quantidade_kg
        nova_quantidade = q3(data.get('quantidade_kg'))

        # Validar nova quantidade
        if not nova_quantidade or nova_quantidade <= 0:
            return JsonResponse({
                'success': False, 
                'message': 'A quantidade deve ser um número positivo.'
            }, status=400)

        # Ajustar estoque se a quantidade mudou
        if nova_quantidade != quantidade_anterior and obj.produto_racao:
            diferenca = nova_quantidade - quantidade_anterior
            try:
                produto = Produto.objects.select_for_update().get(pk=obj.produto_racao.pk)
                
                # Verificar estoque se for aumento
                if diferenca > 0 and hasattr(produto, 'quantidade_estoque'):
                    if produto.quantidade_estoque < diferenca:
                        return JsonResponse({
                            'success': False,
                            'message': f'Estoque insuficiente para aumento. Disponível: {produto.quantidade_estoque:.3f} kg'
                        }, status=400)
                
                # Atualizar estoque
                Produto.objects.filter(pk=obj.produto_racao.pk).update(
                    quantidade_saidas=F('quantidade_saidas') + diferenca
                )
            except Produto.DoesNotExist:
                logger.error(f"Produto {obj.produto_racao.pk} não encontrado para atualização de estoque")
            except DatabaseError as e:
                logger.error(f"Erro ao atualizar estoque: {e}")
                raise Exception("Falha ao atualizar estoque")

        # Atualizar o objeto
        obj.quantidade_kg = nova_quantidade
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

        ld = lote_diario
        # Mantém o snapshot do LoteDiario alinhado ao lançamento editado
        lote_diario.racao_realizada = obj.produto_racao

        # Chamar a função única de recálculo
        recalcular_lote_diario_real(ld, request.user)

        # --- LÓGICA DE ENCADEAMENTO D -> D+1 ---
        proximo_dia = lote_diario.data_evento + timedelta(days=1)
        proximo = LoteDiario.objects.filter(lote=lote, data_evento=proximo_dia).first()
        if proximo:
            base_bio = lote_diario.biomassa_real if lote_diario.biomassa_real is not None else lote_diario.biomassa_projetada
            base_peso = lote_diario.peso_medio_real if lote_diario.peso_medio_real is not None else lote_diario.peso_medio_projetado
            base_qtd = lote_diario.quantidade_real if lote_diario.quantidade_real is not None else lote_diario.quantidade_projetada

            proximo.biomassa_inicial = base_bio
            proximo.peso_medio_inicial = base_peso
            proximo.quantidade_inicial = base_qtd
            proximo.save(update_fields=['biomassa_inicial', 'peso_medio_inicial', 'quantidade_inicial'])

        reprojetar_ciclo_de_vida(lote_diario.lote, lote_diario.data_evento + timedelta(days=1))

        return JsonResponse({
            'success': True, 
            'message': 'Lançamento atualizado e projeção recalculada.'
        })
    except ArracoamentoRealizado.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Lançamento não encontrado.'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'message': 'Formato JSON inválido.'
        }, status=400)
    except Exception as e:
        logger.exception(f"Erro ao atualizar lançamento {pk}: {e}")
        return JsonResponse({
            'success': False, 
            'message': f'Erro ao atualizar lançamento: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
@permission_required('producao.view_arracoamentorealizado', raise_exception=True)
def api_get_arracoamento_realizado(request, pk):
    try:
        obj = ArracoamentoRealizado.objects.select_related(
            'lote_diario__lote',
            'produto_racao'
        ).get(pk=pk)
        
        data = {
            'id': obj.id,
            'lote_diario_id': obj.lote_diario.id,
            'lote_nome': obj.lote_diario.lote.nome,
            'produto_racao_id': obj.produto_racao.id if obj.produto_racao else None,
            'produto_racao_nome': obj.produto_racao.nome if obj.produto_racao else 'N/A',
            'quantidade_kg': float(obj.quantidade_kg),
            'data_realizacao': (obj.data_realizacao or obj.data_lancamento).isoformat(),
            'observacoes': obj.observacoes,
            'usuario_lancamento': obj.usuario_lancamento.username if obj.usuario_lancamento else None,
            'usuario_edicao': obj.usuario_edicao.username if obj.usuario_edicao else None,
            'data_edicao': obj.data_edicao.isoformat() if obj.data_edicao else None,
        }
        return JsonResponse({'success': True, 'data': data})
    except ArracoamentoRealizado.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Lançamento não encontrado.'
        }, status=404)
    except Exception as e:
        logger.exception(f"Erro ao buscar lançamento {pk}: {e}")
        return JsonResponse({
            'success': False, 
            'message': f'Erro ao buscar lançamento: {str(e)}'
        }, status=500)
        
# views_arracoamento.py (adicione esta função)

@login_required
@require_http_methods(["GET"])
@permission_required('producao.view_faseproducao', raise_exception=True)
def api_fases_com_tanques(request):
    """
    Retorna todas as fases de produção com seus respectivos tanques
    """
    try:
        from .models import FaseProducao, Tanque
        
        # Busca todas as fases ativas
        fases = FaseProducao.objects.filter(ativa=True).order_by('nome')
        
        fases_data = []
        for fase in fases:
            # Busca tanques associados a esta fase
            tanques = Tanque.objects.filter(
                fase_producao_atual=fase,
                ativo=True
            ).values_list('nome', flat=True)
            
            fases_data.append({
                'id': fase.id,
                'nome': fase.nome,
                'tanques': list(tanques) if tanques else ['Nenhum tanque']
            })
        
        return JsonResponse({
            'success': True,
            'fases': fases_data
        })
        
    except Exception as e:
        logger.exception(f"Erro ao buscar fases com tanques: {e}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
@permission_required('producao.view_parametroambientaldiario', raise_exception=True)
def api_ambiente_get(request):
    """
    Retorna os parâmetros ambientais para uma data específica
    """
    try:
        data_str = request.GET.get('data')
        if not data_str:
            return JsonResponse({
                'success': False,
                'message': 'Parâmetro data é obrigatório'
            }, status=400)
            
        data = datetime.strptime(data_str, '%Y-%m-%d').date()
        
        # Busca todos os parâmetros ambientais para esta data
        parametros = ParametroAmbientalDiario.objects.filter(
            data=data
        ).select_related('fase')
        
        fases_data = []
        for p in parametros:
            fases_data.append({
                'fase_id': p.fase_id,
                'fase_nome': p.fase.nome if p.fase else None,
                'od_1': float(p.od_1) if p.od_1 else None,
                'od_2': float(p.od_2) if p.od_2 else None,
                'od_3': float(p.od_3) if p.od_3 else None,
                'od_4': float(p.od_4) if p.od_4 else None,
                'od_5': float(p.od_5) if p.od_5 else None,
                'temp_1': float(p.temp_1) if p.temp_1 else None,
                'temp_2': float(p.temp_2) if p.temp_2 else None,
                'temp_3': float(p.temp_3) if p.temp_3 else None,
                'temp_4': float(p.temp_4) if p.temp_4 else None,
                'temp_5': float(p.temp_5) if p.temp_5 else None,
                'ph': float(p.ph) if p.ph else None,
                'amonia': float(p.amonia) if p.amonia else None,
                'nitrito': float(p.nitrito) if p.nitrito else None,
            })
        
        return JsonResponse({
            'success': True,
            'data': data_str,
            'fases': fases_data
        })
        
    except Exception as e:
        logger.exception(f"Erro ao buscar parâmetros ambientais: {e}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@permission_required('producao.add_parametroambientaldiario', raise_exception=True)
def api_ambiente_upsert(request):
    """
    Cria ou atualiza parâmetros ambientais para uma data
    """
    try:
        data = json.loads(request.body)
        data_str = data.get('data')
        fases = data.get('fases', [])
        
        if not data_str:
            return JsonResponse({
                'success': False,
                'message': 'Data é obrigatória'
            }, status=400)
            
        data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
        
        with transaction.atomic():
            for fase_data in fases:
                fase_id = fase_data.get('fase_id')
                if not fase_id:
                    continue
                    
                # Busca ou cria o registro
                param, created = ParametroAmbientalDiario.objects.update_or_create(
                    data=data_obj,
                    fase_id=fase_id,
                    defaults={
                        'od_1': fase_data.get('od_1'),
                        'od_2': fase_data.get('od_2'),
                        'od_3': fase_data.get('od_3'),
                        'od_4': fase_data.get('od_4'),
                        'od_5': fase_data.get('od_5'),
                        'temp_1': fase_data.get('temp_1'),
                        'temp_2': fase_data.get('temp_2'),
                        'temp_3': fase_data.get('temp_3'),
                        'temp_4': fase_data.get('temp_4'),
                        'temp_5': fase_data.get('temp_5'),
                        'ph': fase_data.get('ph'),
                        'amonia': fase_data.get('amonia'),
                        'nitrito': fase_data.get('nitrito'),
                        'usuario_registro': request.user,
                    }
                )
        
        return JsonResponse({
            'success': True,
            'message': 'Parâmetros ambientais salvos com sucesso'
        })
        
    except Exception as e:
        logger.exception(f"Erro ao salvar parâmetros ambientais: {e}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)











