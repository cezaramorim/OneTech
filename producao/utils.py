from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib import messages
from common.messages_utils import get_app_messages
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
import json
from decimal import Decimal
from .models import Lote, LoteDiario, CurvaCrescimento, CurvaCrescimentoDetalhe, EventoManejo
from datetime import date, timedelta
import logging

# Importa as novas funções de cálculo padronizadas
from .utils_uom import calc_biomassa_kg, calc_racao_kg, calc_fcr, g_to_kg, q2, q3


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

            objects_to_delete = self.model.objects.filter(pk__in=ids)
            deleted_names = [str(obj) for obj in objects_to_delete]

            deleted_count, _ = objects_to_delete.delete()

            if deleted_count > 0:
                if len(deleted_names) == 1:
                    message_detail = f"'{deleted_names[0]}'"
                else:
                    message_detail = f"'{', '.join(deleted_names)}'"
                message = app_messages.success_deleted(self.model._meta.verbose_name_plural, message_detail)
            else:
                message = app_messages.error('Nenhum item foi excluído.')
            
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
    quantidade_projetada_corrente = lote.quantidade_inicial
    peso_corrente_g = lote.peso_medio_inicial

    registros_lote_diario = []

    for detalhe in detalhes_para_projetar:
        if detalhe.periodo_dias <= 0:
            continue

        mortalidade_diaria_perc = q3(detalhe.mortalidade_presumida_perc / Decimal(detalhe.periodo_dias) if detalhe.periodo_dias > 0 else Decimal('0'))

        for _ in range(detalhe.periodo_dias):
            if peso_corrente_g >= detalhe.peso_final:
                continue

            biomassa_inicio_dia_kg = calc_biomassa_kg(quantidade_projetada_corrente, peso_corrente_g)
            racao_sugerida_kg = calc_racao_kg(biomassa_inicio_dia_kg, detalhe.arracoamento_biomassa_perc)

            tca_da_curva = detalhe.tca
            gpd_calculado_g = Decimal('0.0')
            if tca_da_curva and tca_da_curva > 0:
                ganho_biomassa_dia_kg = q3(racao_sugerida_kg / tca_da_curva)
                if quantidade_projetada_corrente > 0:
                    gpd_calculado_g = q3((ganho_biomassa_dia_kg * 1000) / quantidade_projetada_corrente)

            peso_final_dia_g = peso_corrente_g + gpd_calculado_g
            
            mortalidade_do_dia = quantidade_projetada_corrente * (mortalidade_diaria_perc / 100)
            quantidade_final_dia = quantidade_projetada_corrente - mortalidade_do_dia
            
            biomassa_final_dia_kg = calc_biomassa_kg(quantidade_final_dia, peso_final_dia_g)
            gpt_projetado_valor_g = peso_final_dia_g - lote.peso_medio_inicial

            registros_lote_diario.append(
                LoteDiario(
                    lote=lote,
                    data_evento=data_corrente,
                    quantidade_inicial=quantidade_projetada_corrente,
                    peso_medio_inicial=peso_corrente_g,
                    biomassa_inicial=q3(biomassa_inicio_dia_kg),
                    quantidade_projetada=quantidade_final_dia,
                    peso_medio_projetado=peso_final_dia_g,
                    biomassa_projetada=q3(biomassa_final_dia_kg),
                    gpd_projetado=gpd_calculado_g,
                    gpt_projetado=gpt_projetado_valor_g,
                    racao_sugerida=detalhe.racao,
                    racao_sugerida_kg=racao_sugerida_kg,
                    conversao_alimentar_projetada=tca_da_curva
                )
            )

            peso_corrente_g = peso_final_dia_g
            quantidade_projetada_corrente = quantidade_final_dia
            data_corrente += timedelta(days=1)
    
    if registros_lote_diario:
        LoteDiario.objects.bulk_create(registros_lote_diario)

def get_detalhe_curva_para_peso(curva: CurvaCrescimento, peso_em_g: Decimal):
    """
    Encontra o detalhe da curva de crescimento correspondente a um peso específico em gramas.
    """
    if not curva:
        return None
    
    detalhe = curva.detalhes.filter(
        peso_inicial__lte=peso_em_g,
        peso_final__gt=peso_em_g
    ).first()
    
    if not detalhe:
        detalhe = curva.detalhes.filter(
            peso_inicial__lte=peso_em_g
        ).order_by('-peso_inicial').first()

    return detalhe

def sugerir_para_lote(lote: Lote) -> dict:
    """
    Gera uma sugestão de arraçoamento para um lote, usando o peso real mais recente.
    """
    logging.info(f"[SUGESTÃO] Lote {lote.id}: Iniciando. Qtd: {lote.quantidade_atual}")
    if not lote.ativo or lote.quantidade_atual <= 0:
        return {'error': 'Lote inválido ou inativo.'}
    if not lote.curva_crescimento:
        return {'error': 'Lote sem curva de crescimento.'}

    ultimo_registro_diario = LoteDiario.objects.filter(
        lote=lote, 
        peso_medio_real__isnull=False
    ).order_by('-data_evento').first()

    peso_base_g = lote.peso_medio_inicial
    if ultimo_registro_diario:
        peso_base_g = ultimo_registro_diario.peso_medio_real

    detalhe_curva = get_detalhe_curva_para_peso(lote.curva_crescimento, peso_base_g)
    logging.info(f"[SUGESTÃO] Lote {lote.id}: Peso base: {peso_base_g}g. Detalhe curva: {detalhe_curva}")

    if not detalhe_curva:
        return {'error': f'Nenhum ponto na curva para o peso de {peso_base_g}g.'}

    percentual_pv = detalhe_curva.arracoamento_biomassa_perc
    produto_racao = detalhe_curva.racao

    if not percentual_pv or percentual_pv <= 0:
        return {'error': f'Ponto da curva para {peso_base_g}g sem % arraçoamento.'}
    if not produto_racao:
        return {'error': f'Ponto da curva para {peso_base_g}g sem ração definida.'}

    # --- CÁLCULO PADRONIZADO ---
    biomassa_kg = calc_biomassa_kg(lote.quantidade_atual, peso_base_g)
    quantidade_sugerida_kg = calc_racao_kg(biomassa_kg, percentual_pv)
    logging.info(f"[SUGESTÃO] Lote {lote.id}: Biomassa: {biomassa_kg}kg, Ração Sugerida: {quantidade_sugerida_kg}kg")
    # --- FIM ---

    return {
        'lote': lote,
        'produto_racao': produto_racao,
        'quantidade_kg': quantidade_sugerida_kg,
        'biomassa_kg': biomassa_kg,
        'percentual_pv': percentual_pv
    }


def reprojetar_ciclo_de_vida(lote: Lote, data_de_inicio: date):
    """
    Recalcula a projeção de vida de um lote a partir de uma data, usando o último estado real.
    """
    if not lote.curva_crescimento:
        return

    ultimo_estado_real = LoteDiario.objects.filter(
        lote=lote,
        data_evento__lt=data_de_inicio,
        peso_medio_real__isnull=False
    ).order_by('-data_evento').first()

    if ultimo_estado_real:
        peso_base_g = ultimo_estado_real.peso_medio_real
        quantidade_base = ultimo_estado_real.quantidade_real if ultimo_estado_real.quantidade_real is not None else lote.quantidade_atual
    else:
        peso_base_g = lote.peso_medio_inicial
        quantidade_base = lote.quantidade_inicial

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
    quantidade_projetada_corrente = quantidade_base
    peso_corrente_g = peso_base_g

    registros_lote_diario = []

    for detalhe in detalhes_para_projetar:
        if detalhe.periodo_dias <= 0: continue

        mortalidade_diaria_perc = q3(detalhe.mortalidade_presumida_perc / Decimal(detalhe.periodo_dias) if detalhe.periodo_dias > 0 else Decimal('0'))

        for _ in range(detalhe.periodo_dias):
            if peso_corrente_g >= detalhe.peso_final: continue

            # --- CÁLCULOS PADRONIZADOS ---
            biomassa_inicio_dia_kg = calc_biomassa_kg(quantidade_projetada_corrente, peso_corrente_g)
            racao_sugerida_kg = calc_racao_kg(biomassa_inicio_dia_kg, detalhe.arracoamento_biomassa_perc)

            tca_da_curva = detalhe.tca
            gpd_calculado_g = Decimal('0.0')
            if tca_da_curva and tca_da_curva > 0:
                ganho_biomassa_dia_kg = q3(racao_sugerida_kg / tca_da_curva)
                if quantidade_projetada_corrente > 0:
                    # Converte ganho de biomassa (kg) para ganho de peso individual (g)
                    gpd_calculado_g = q3((ganho_biomassa_dia_kg * 1000) / quantidade_projetada_corrente)
            
            peso_final_dia_g = peso_corrente_g + gpd_calculado_g
            mortalidade_do_dia = quantidade_projetada_corrente * (mortalidade_diaria_perc / 100)
            quantidade_final_dia = quantidade_projetada_corrente - mortalidade_do_dia
            biomassa_final_dia_kg = calc_biomassa_kg(quantidade_final_dia, peso_final_dia_g)
            gpt_projetado_valor_g = peso_final_dia_g - lote.peso_medio_inicial
            # --- FIM ---

            registros_lote_diario.append(
                LoteDiario(
                    lote=lote, data_evento=data_corrente,
                    quantidade_inicial=quantidade_projetada_corrente,
                    peso_medio_inicial=peso_corrente_g,
                    biomassa_inicial=biomassa_inicio_dia_kg,
                    quantidade_projetada=quantidade_final_dia,
                    peso_medio_projetado=peso_final_dia_g,
                    biomassa_projetada=biomassa_final_dia_kg,
                    gpd_projetado=gpd_calculado_g,
                    gpt_projetado=gpt_projetado_valor_g,
                    racao_sugerida=detalhe.racao,
                    racao_sugerida_kg=racao_sugerida_kg,
                    conversao_alimentar_projetada=tca_da_curva
                )
            )

            peso_corrente_g = peso_final_dia_g
            quantidade_projetada_corrente = quantidade_final_dia
            data_corrente += timedelta(days=1)
    
    if registros_lote_diario:
        LoteDiario.objects.bulk_create(registros_lote_diario)

def _apurar_quantidade_real_no_dia(lote_diario: LoteDiario) -> Decimal:
    lote = lote_diario.lote
    data = lote_diario.data_evento

    qtd_ini = Decimal(str(lote_diario.quantidade_inicial or 0))

    eventos = EventoManejo.objects.filter(lote=lote, data_evento=data)

    entradas = Decimal('0')
    saidas   = Decimal('0')

    # A data de povoamento do lote, para comparação.
    data_povoamento_lote = lote.data_povoamento

    for ev in eventos:
        q = Decimal(str(ev.quantidade or 0))
        t = (ev.tipo_evento or '').lower()
        mov = (ev.tipo_movimento or '').lower()

        # CORREÇÃO: No dia do povoamento inicial do lote, o evento 'Povoamento'
        # não deve ser somado, pois ele já está refletido na 'quantidade_inicial'.
        if data == data_povoamento_lote and t == 'povoamento':
            continue

        # ENTRADAS
        if t in ('povoamento', 'classificacao') and mov == 'entrada':
            entradas += q
        elif t == 'transferencia' and mov == 'entrada':
            entradas += q

        # SAÍDAS
        elif t in ('mortalidade', 'despesca') or (t == 'transferencia' and mov == 'saida'):
            saidas += q

    qtd_fim = qtd_ini + entradas - saidas
    if qtd_fim < 0:
        qtd_fim = Decimal('0')
    return qtd_fim
