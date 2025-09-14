from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib import messages
from common.messages_utils import get_app_messages
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
import json


class AjaxFormMixin:
    """
    Mixin para CreateView e UpdateView que lida com submissões de formulário
    via AJAX, retornando JSON, ou redirecionando em requisições normais.
    """
    success_url = None

    def form_valid(self, form):
        app_messages = get_app_messages(self.request)
        self.object = form.save()
        
        if hasattr(self, 'object') and self.object.pk: # Se o objeto foi salvo (update)
            message = app_messages.success_updated(self.object)
        else: # Se é um novo objeto (create)
            message = app_messages.success_created(self.object)

        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': message,
                'redirect_url': str(self.get_success_url())
            })
        return super().form_valid(form)

    def form_invalid(self, form):
        app_messages = get_app_messages(self.request)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            message = app_messages.error('Erro ao salvar. Verifique os campos.')
            return JsonResponse({'success': False, 'message': message, 'errors': form.errors}, status=400)
        app_messages.error('Erro ao salvar. Verifique os campos.')
        return super().form_invalid(form)


class BulkDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    View genérica para exclusão em massa de objetos via POST com JSON.
    Espera uma lista de IDs.
    """
    model = None
    permission_required = ""
    success_url_name = "" # Nome da URL para redirecionamento (ex: 'producao:lista_tanques')
    raise_exception = True

    def post(self, request, *args, **kwargs):
        app_messages = get_app_messages(request)
        try:
            data = json.loads(request.body)
            ids = data.get('ids', [])
            if not ids:
                message = app_messages.error('Nenhum item selecionado para exclusão.')
                return JsonResponse({'success': False, 'message': message}, status=400)

            # Recupera os nomes dos objetos antes de excluí-los
            objects_to_delete = self.model.objects.filter(pk__in=ids)
            deleted_names = [str(obj) for obj in objects_to_delete] # Converte para string para pegar o __str__ do modelo

            deleted_count, _ = objects_to_delete.delete()

            if deleted_count > 0:
                if len(deleted_names) == 1:
                    message_detail = f"'{deleted_names[0]}'"
                else:
                    message_detail = f"'{', '.join(deleted_names)}'"
                message = app_messages.success_deleted(self.model._meta.verbose_name_plural, message_detail)
            else:
                message = app_messages.error('Nenhum item foi excluído.') # Caso não encontre nenhum para excluir
            
            return JsonResponse({
                'success': True, 
                'message': message,
                'redirect_url': str(reverse_lazy(self.success_url_name))
            })
        except json.JSONDecodeError:
            message = app_messages.error('Requisição JSON inválida.')
            return JsonResponse({'success': False, 'message': message}, status=400)
        except Exception as e:
            message = app_messages.error(f'Ocorreu um erro inesperado: {e}')
            return JsonResponse({'success': False, 'message': message}, status=500)


# -*- coding: utf-8 -*-
from decimal import Decimal
from .models import Lote, LoteDiario, CurvaCrescimento, CurvaCrescimentoDetalhe
from datetime import date, timedelta, timedelta
from decimal import Decimal
import logging

def projetar_ciclo_de_vida_lote(lote: Lote):
    """
    Cria ou recria a projeção de vida completa para um lote, usando a TCA da curva como fonte da verdade para o crescimento.
    """
    if not lote.curva_crescimento:
        raise ValueError("Lote não possui curva de crescimento associada.")

    LoteDiario.objects.filter(lote=lote, data_evento__gte=lote.data_povoamento).delete()

    detalhes_curva = lote.curva_crescimento.detalhes.order_by('periodo_semana')
    if not detalhes_curva.exists():
        return

    start_index = 0
    for i, detalhe in enumerate(detalhes_curva):
        if detalhe.peso_inicial <= lote.peso_medio_inicial and detalhe.peso_final > lote.peso_medio_inicial:
            start_index = i
            break
    
    detalhes_para_projetar = detalhes_curva[start_index:]

    data_corrente = lote.data_povoamento
    quantidade_constante_projetada = lote.quantidade_inicial
    peso_corrente_g = lote.peso_medio_inicial

    registros_lote_diario = []

    for detalhe in detalhes_para_projetar:
        if detalhe.periodo_dias <= 0:
            continue

        for _ in range(detalhe.periodo_dias):
            if peso_corrente_g >= detalhe.peso_final:
                continue

            # --- LÓGICA FINAL (TCA-Driven) ---
            # 1. Calcular ração com base no estado do INÍCIO do dia.
            biomassa_inicio_dia_kg = (quantidade_constante_projetada * peso_corrente_g) / 1000
            racao_sugerida_kg = biomassa_inicio_dia_kg * (detalhe.arracoamento_biomassa_perc / 100)

            # 2. Obter TCA da curva e CALCULAR o ganho de peso do dia.
            tca_da_curva = detalhe.tca
            gpd_calculado = Decimal('0.0')
            if tca_da_curva and tca_da_curva > 0:
                ganho_biomassa_dia_kg = racao_sugerida_kg / tca_da_curva
                if quantidade_constante_projetada > 0:
                    gpd_calculado = (ganho_biomassa_dia_kg * 1000) / quantidade_constante_projetada

            # 3. Calcular o estado do FIM do dia.
            peso_final_dia_g = peso_corrente_g + gpd_calculado
            biomassa_final_dia_kg = (quantidade_constante_projetada * peso_final_dia_g) / 1000

            # 4. Calcular GPT projetado com base no peso do FIM do dia.
            gpt_projetado_valor = peso_final_dia_g - lote.peso_medio_inicial

            # 5. Criar o registro do dia.
            registros_lote_diario.append(
                LoteDiario(
                    lote=lote,
                    data_evento=data_corrente,
                    quantidade_projetada=quantidade_constante_projetada,
                    peso_medio_projetado=peso_final_dia_g,
                    biomassa_projetada=biomassa_final_dia_kg,
                    gpd_projetado=gpd_calculado,
                    gpt_projetado=gpt_projetado_valor,
                    racao_sugerida=detalhe.racao,
                    racao_sugerida_kg=racao_sugerida_kg,
                    conversao_alimentar_projetada=tca_da_curva
                )
            )

            # 6. ATUALIZAR o estado para o PRÓXIMO dia.
            peso_corrente_g = peso_final_dia_g
            data_corrente += timedelta(days=1)
    
    if registros_lote_diario:
        LoteDiario.objects.bulk_create(registros_lote_diario)

def reprojetar_ciclo_de_vida(lote: Lote, data_de_inicio: date):
    """
    Recalcula a projeção de vida de um lote a partir de uma data específica,
    usando o último estado real conhecido como ponto de partida.
    """
    if not lote.curva_crescimento:
        return

    # 1. Encontrar o ponto de partida (o último registro com dados reais)
    ultimo_estado_real = LoteDiario.objects.filter(
        lote=lote,
        data_evento__lt=data_de_inicio,
        peso_medio_real__isnull=False
    ).order_by('-data_evento').first()

    # --- DEBUG LOG ---
    logging.info(f"[DEBUG REPROJEÇÃO] Chamada com data_de_inicio: {data_de_inicio}")
    if ultimo_estado_real:
        logging.info(f"[DEBUG REPROJEÇÃO] ultimo_estado_real encontrado para data: {ultimo_estado_real.data_evento} com peso_real: {ultimo_estado_real.peso_medio_real}")
    else:
        logging.info(f"[DEBUG REPROJEÇÃO] ultimo_estado_real NÃO encontrado. Usando peso inicial do lote.")
    # --- FIM DEBUG LOG ---

    if ultimo_estado_real:
        peso_base_g = ultimo_estado_real.peso_medio_real
    else:
        peso_base_g = lote.peso_medio_inicial

    LoteDiario.objects.filter(lote=lote, data_evento__gte=data_de_inicio).delete()

    detalhes_curva = lote.curva_crescimento.detalhes.order_by('periodo_semana')
    if not detalhes_curva.exists():
        return

    start_index = 0
    for i, detalhe in enumerate(detalhes_curva):
        if detalhe.peso_inicial <= peso_base_g and detalhe.peso_final > peso_base_g:
            start_index = i
            break

    detalhes_para_projetar = detalhes_curva[start_index:]

    data_corrente = data_de_inicio
    quantidade_constante_projetada = lote.quantidade_inicial
    peso_corrente_g = peso_base_g

    registros_lote_diario = []

    for detalhe in detalhes_para_projetar:
        if detalhe.periodo_dias <= 0:
            continue

        for _ in range(detalhe.periodo_dias):
            if peso_corrente_g >= detalhe.peso_final:
                continue

            # --- LÓGICA FINAL (TCA-Driven) ---
            biomassa_inicio_dia_kg = (quantidade_constante_projetada * peso_corrente_g) / 1000
            racao_sugerida_kg = biomassa_inicio_dia_kg * (detalhe.arracoamento_biomassa_perc / 100)

            tca_da_curva = detalhe.tca
            gpd_calculado = Decimal('0.0')
            if tca_da_curva and tca_da_curva > 0:
                ganho_biomassa_dia_kg = racao_sugerida_kg / tca_da_curva
                if quantidade_constante_projetada > 0:
                    gpd_calculado = (ganho_biomassa_dia_kg * 1000) / quantidade_constante_projetada

            peso_final_dia_g = peso_corrente_g + gpd_calculado
            biomassa_final_dia_kg = (quantidade_constante_projetada * peso_final_dia_g) / 1000

            gpt_projetado_valor = peso_final_dia_g - lote.peso_medio_inicial

            registros_lote_diario.append(
                LoteDiario(
                    lote=lote,
                    data_evento=data_corrente,
                    quantidade_projetada=quantidade_constante_projetada,
                    peso_medio_projetado=peso_final_dia_g,
                    biomassa_projetada=biomassa_final_dia_kg,
                    gpd_projetado=gpd_calculado,
                    gpt_projetado=gpt_projetado_valor,
                    racao_sugerida=detalhe.racao,
                    racao_sugerida_kg=racao_sugerida_kg,
                    conversao_alimentar_projetada=tca_da_curva
                )
            )

            peso_corrente_g = peso_final_dia_g
            data_corrente += timedelta(days=1)
    
    if registros_lote_diario:
        LoteDiario.objects.bulk_create(registros_lote_diario)

def get_detalhe_curva_para_peso(curva: CurvaCrescimento, peso_em_gramas: Decimal):
    """
    Encontra o detalhe da curva de crescimento correspondente a um peso específico.
    """
    if not curva:
        return None
    
    # A consulta agora busca o detalhe que engloba o peso médio.
    # A lógica é: peso_inicial <= peso_em_gramas < peso_final
    detalhe = curva.detalhes.filter(
        peso_inicial__lte=peso_em_gramas,
        peso_final__gt=peso_em_gramas
    ).first()
    
    if not detalhe:
        # Fallback: Se não encontrar um intervalo exato, pega o mais próximo (sem passar)
        detalhe = curva.detalhes.filter(
            peso_inicial__lte=peso_em_gramas
        ).order_by('-peso_inicial').first()

    return detalhe

def sugerir_para_lote(lote: Lote) -> dict:
    """
    Gera uma sugestão de arraçoamento completa para um lote específico,
    usando o dado de peso real mais recente disponível no LoteDiario.
    """
    logging.info(f"Iniciando sugerir_para_lote para lote {lote.id} (Qtd: {lote.quantidade_atual}).")
    if not lote.ativo or lote.quantidade_atual <= 0:
        return {'error': 'Lote inválido.'}
    if not lote.curva_crescimento:
        return {'error': 'Lote não possui curva de crescimento associada.'}

    # --- LÓGICA CORRIGIDA: Usa o peso real mais recente do LoteDiario ---
    ultimo_registro_diario = LoteDiario.objects.filter(
        lote=lote, 
        peso_medio_real__isnull=False
    ).order_by('-data_evento').first()

    peso_base_para_sugestao = lote.peso_medio_inicial
    if ultimo_registro_diario:
        peso_base_para_sugestao = ultimo_registro_diario.peso_medio_real
    # --- FIM DA CORREÇÃO ---

    detalhe_curva = get_detalhe_curva_para_peso(lote.curva_crescimento, peso_base_para_sugestao)
    logging.info(f"Peso base para sugestão: {peso_base_para_sugestao}. Detalhe da curva encontrado: Período {detalhe_curva.periodo_semana if detalhe_curva else 'Nenhum'}")

    if not detalhe_curva:
        return {'error': f'Nenhum ponto de crescimento na curva corresponde ao peso de {peso_base_para_sugestao}g.'}

    percentual_pv = detalhe_curva.arracoamento_biomassa_perc
    produto_racao = detalhe_curva.racao

    if not percentual_pv or percentual_pv <= 0:
        return {'error': f'O ponto de crescimento para {peso_base_para_sugestao}g não tem um percentual de arraçoamento definido.'}
    
    if not produto_racao:
        return {'error': f'O ponto de crescimento para {peso_base_para_sugestao}g não tem uma ração definida.'}

    # Usa a quantidade ATUAL do lote para o cálculo da biomassa
    biomassa_kg = (lote.quantidade_atual * peso_base_para_sugestao) / Decimal('1000')
    quantidade_sugerida_kg = biomassa_kg * (percentual_pv / Decimal('100'))
    logging.info(f"Sugestão calculada para lote {lote.id}: {quantidade_sugerida_kg} kg de {produto_racao.nome if produto_racao else 'N/A'}.")

    return {
        'lote': lote,
        'produto_racao': produto_racao,
        'quantidade_kg': quantidade_sugerida_kg.quantize(Decimal('0.001')),
        'biomassa_kg': biomassa_kg,
        'percentual_pv': percentual_pv
    }