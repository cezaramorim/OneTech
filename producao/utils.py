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
from .models import Lote, LoteDiario, CurvaCrescimentoDetalhe
from datetime import date, timedelta, timedelta
from decimal import Decimal
import logging

def projetar_ciclo_de_vida_lote(lote: Lote):
    """
    Cria ou recria a projeção de vida completa para um lote com base na sua curva de crescimento.
    """
    if not lote.curva_crescimento:
        raise ValueError("Lote não possui curva de crescimento associada.")

    # Apaga projeções futuras para garantir que a projeção seja sempre a mais recente
    LoteDiario.objects.filter(lote=lote, data_evento__gte=lote.data_povoamento).delete()

    detalhes_curva = lote.curva_crescimento.detalhes.order_by('periodo_semana')
    if not detalhes_curva.exists():
        return # Não faz nada se a curva não tiver detalhes

    # Variáveis de estado para a projeção
    data_corrente = lote.data_povoamento
    quantidade_corrente = lote.quantidade_inicial
    peso_corrente_g = lote.peso_medio_inicial

    registros_lote_diario = []

    for detalhe in detalhes_curva:
        if detalhe.periodo_dias <= 0:
            continue

        # GPD (Ganho de Peso Diário) para este período da curva
        gpd_periodo = detalhe.gpd
        mortalidade_diaria_perc = detalhe.mortalidade_presumida_perc / Decimal(detalhe.periodo_dias) if detalhe.periodo_dias > 0 else Decimal(0)

        for _ in range(detalhe.periodo_dias):
            # 1. Calcula mortalidade e ajusta quantidade
            mortalidade_projetada = quantidade_corrente * (mortalidade_diaria_perc / 100)
            quantidade_corrente -= mortalidade_projetada

            # 2. Calcula ganho de peso e ajusta peso médio
            peso_corrente_g += gpd_periodo

            # Calcula GPT projetado
            gpt_projetado_valor = peso_corrente_g - lote.peso_medio_inicial

            # 3. Calcula biomassa
            biomassa_projetada_kg = (quantidade_corrente * peso_corrente_g) / 1000

            # 4. Calcula ração sugerida
            racao_sugerida_kg = biomassa_projetada_kg * (detalhe.arracoamento_biomassa_perc / 100)

            # 5. Cria o objeto LoteDiario em memória
            registros_lote_diario.append(
                LoteDiario(
                    lote=lote,
                    data_evento=data_corrente,
                    quantidade_projetada=quantidade_corrente,
                    peso_medio_projetado=peso_corrente_g,
                    biomassa_projetada=biomassa_projetada_kg,
                    gpd_projetado=gpd_periodo,
                    gpt_projetado=gpt_projetado_valor,
                    racao_sugerida=detalhe.racao,
                    racao_sugerida_kg=racao_sugerida_kg,
                    # TODO: Calcular e adicionar conversao_alimentar_projetada
                )
            )
            data_corrente += timedelta(days=1)
    
    # 6. Salva todos os registros no banco de dados de uma vez
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
        quantidade_real__isnull=False,
        peso_medio_real__isnull=False
    ).order_by('-data_evento').first()

    if ultimo_estado_real:
        data_base = ultimo_estado_real.data_evento
        quantidade_base = ultimo_estado_real.quantidade_real
        peso_base_g = ultimo_estado_real.peso_medio_real
    else:
        # Fallback para o estado inicial do lote
        data_base = lote.data_povoamento
        quantidade_base = lote.quantidade_inicial
        peso_base_g = lote.peso_medio_inicial

    # 2. Apagar projeções futuras a partir da data de início do recálculo
    LoteDiario.objects.filter(lote=lote, data_evento__gte=data_de_inicio).delete()

    # 3. Encontrar o ponto na curva de crescimento correspondente aos dias de cultivo
    dias_desde_povoamento_base = (data_base - lote.data_povoamento).days
    detalhes_curva = lote.curva_crescimento.detalhes.order_by('periodo_semana')
    if not detalhes_curva.exists():
        return

    # Lógica para avançar na curva até o ponto de início da re-projeção
    dias_a_pular = (data_de_inicio - data_base).days
    
    # Simula o crescimento desde a data base até a data de início da re-projeção
    quantidade_corrente = quantidade_base
    peso_corrente_g = peso_base_g

    # Encontra o detalhe da curva correspondente à data_base
    detalhe_base = None
    dias_acumulados_curva = 0
    for det in detalhes_curva:
        dias_acumulados_curva += det.periodo_dias
        if dias_acumulados_curva >= dias_desde_povoamento_base:
            detalhe_base = det
            break

    if not detalhe_base:
        # Se a data base está além do fim da curva, não há mais projeção
        return

    # Inicia a nova projeção a partir do estado simulado
    data_corrente = data_de_inicio
    registros_lote_diario = []

    # Itera sobre os detalhes da curva a partir do detalhe_base
    # e continua a projeção
    for detalhe in detalhes_curva:
        # Pula os detalhes da curva que já passaram
        if detalhe.periodo_semana < detalhe_base.periodo_semana:
            continue

        gpd_periodo = detalhe.gpd
        mortalidade_diaria_perc = detalhe.mortalidade_presumida_perc / Decimal(detalhe.periodo_dias) if detalhe.periodo_dias > 0 else Decimal(0)

        for i in range(detalhe.periodo_dias):
            # Se a data corrente já passou da data de início da re-projeção, começa a projetar
            if data_corrente >= data_de_inicio:
                # 1. Calcula mortalidade e ajusta quantidade
                mortalidade_projetada = quantidade_corrente * (mortalidade_diaria_perc / 100)
                quantidade_corrente -= mortalidade_projetada

                # 2. Calcula ganho de peso e ajusta peso médio
                peso_corrente_g += gpd_periodo

                # Calcula GPT projetado
                gpt_projetado_valor = peso_corrente_g - lote.peso_medio_inicial

                # 3. Calcula biomassa
                biomassa_projetada_kg = (quantidade_corrente * peso_corrente_g) / 1000

                # 4. Calcula ração sugerida
                racao_sugerida_kg = biomassa_projetada_kg * (detalhe.arracoamento_biomassa_perc / 100)

                # 5. Cria o objeto LoteDiario em memória
                registros_lote_diario.append(
                    LoteDiario(
                        lote=lote,
                        data_evento=data_corrente,
                        quantidade_projetada=quantidade_corrente,
                        peso_medio_projetado=peso_corrente_g,
                        biomassa_projetada=biomassa_projetada_kg,
                        gpd_projetado=gpd_periodo,
                        gpt_projetado=gpt_projetado_valor,
                        racao_sugerida=detalhe.racao,
                        racao_sugerida_kg=racao_sugerida_kg,
                        # TODO: Calcular e adicionar conversao_alimentar_projetada
                    )
                )
            data_corrente += timedelta(days=1)

    if registros_lote_diario:
        LoteDiario.objects.bulk_create(registros_lote_diario)

def get_detalhe_curva_para_peso(lote: Lote):
    """
    Encontra o detalhe da curva de crescimento correspondente ao peso médio atual do lote.
    """
    logging.info(f"Iniciando get_detalhe_curva_para_peso para lote {lote.id} (Peso: {lote.peso_medio_atual}).")
    if not lote.curva_crescimento:
        logging.warning(f"Lote {lote.id} não possui curva de crescimento associada.")
        return None
    
    peso_medio_g = lote.peso_medio_atual
    
    # A consulta agora busca o detalhe que engloba o peso médio.
    # A lógica é: peso_inicial <= peso_medio < peso_final
    detalhe = lote.curva_crescimento.detalhes.filter(
        peso_inicial__lte=peso_medio_g,
        peso_final__gt=peso_medio_g
    ).first()
    
    if detalhe:
        logging.info(f"Detalhe encontrado (primeira tentativa) para lote {lote.id}: Período {detalhe.periodo_semana}.")
    else:
        logging.info(f"Nenhum detalhe encontrado (primeira tentativa) para lote {lote.id}. Tentando fallback.")
        detalhe = lote.curva_crescimento.detalhes.filter(
            peso_inicial__lte=peso_medio_g
        ).order_by('-peso_inicial').first()
        if detalhe:
            logging.info(f"Detalhe encontrado (fallback) para lote {lote.id}: Período {detalhe.periodo_semana}.")
        else:
            logging.warning(f"Nenhum detalhe da curva encontrado (fallback) para o peso {peso_medio_g}g do lote {lote.id}.")

    return detalhe

def sugerir_para_lote(lote: Lote) -> dict:
    """
    Gera uma sugestão de arraçoamento completa para um lote específico,
    baseado DIRETAMENTE na sua curva de crescimento.
    """
    logging.info(f"Iniciando sugerir_para_lote para lote {lote.id} (Qtd: {lote.quantidade_atual}, Peso: {lote.peso_medio_atual}).")
    if not lote.ativo or lote.quantidade_atual <= 0:
        logging.warning(f"Lote {lote.id} inválido (ativo={lote.ativo}, quantidade_atual={lote.quantidade_atual}).")
        return {'error': 'Lote inválido.'}

    detalhe_curva = get_detalhe_curva_para_peso(lote)
    logging.info(f"Resultado de get_detalhe_curva_para_peso para lote {lote.id}: {detalhe_curva.periodo_semana if detalhe_curva else 'Nenhum detalhe encontrado'}")

    if not detalhe_curva:
        logging.warning(f"Nenhum detalhe da curva de crescimento encontrado para o peso {lote.peso_medio_atual}g do lote {lote.id}.")
        return {'error': f'Nenhum ponto de crescimento na curva corresponde ao peso de {lote.peso_medio_atual}g.'}

    percentual_pv = detalhe_curva.arracoamento_biomassa_perc
    produto_racao = detalhe_curva.racao

    if not percentual_pv or percentual_pv <= 0:
        logging.warning(f"Percentual de arraçoamento inválido ({percentual_pv}) para detalhe da curva do lote {lote.id}.")
        return {'error': f'O ponto de crescimento para {lote.peso_medio_atual}g não tem um percentual de arraçoamento definido.'}
    
    if not produto_racao:
        logging.warning(f"Ração não definida para detalhe da curva do lote {lote.id}.")
        return {'error': f'O ponto de crescimento para {lote.peso_medio_atual}g não tem uma ração definida.'}

    biomassa_kg = lote.biomassa_atual / Decimal('1000')
    quantidade_sugerida_kg = biomassa_kg * (percentual_pv / Decimal('100'))
    logging.info(f"Sugestão calculada para lote {lote.id}: {quantidade_sugerida_kg} kg de {produto_racao.nome if produto_racao else 'N/A'}.")

    return {
        'lote': lote,
        'produto_racao': produto_racao,
        'quantidade_kg': quantidade_sugerida_kg.quantize(Decimal('0.001')),
        'biomassa_kg': biomassa_kg,
        'percentual_pv': percentual_pv
    }