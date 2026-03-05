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

            deleted_count = 0
            # Itera para garantir que os sinais de exclusão (post_delete) sejam disparados
            for obj in objects_to_delete:
                obj.delete()
                deleted_count += 1

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

def sugerir_racao_para_dia(lote_diario: LoteDiario) -> dict:
    """
    Gera uma sugestão de arraçoamento para um LoteDiario específico,
    usando a biomassa inicial do dia como base.
    """
    lote = lote_diario.lote
    logging.info(f"[SUGESTÃO] Lote {lote.id}, Dia {lote_diario.data_evento}: Iniciando.")

    # Validações essenciais
    if not lote.ativo:
        return {'error': 'Lote está inativo.'}
    if not lote.curva_crescimento:
        return {'error': 'Lote sem curva de crescimento.'}
    if lote_diario.quantidade_inicial is None or lote_diario.quantidade_inicial <= 0:
        return {'error': 'Quantidade inicial do dia é zero ou inválida.'}
    if lote_diario.peso_medio_inicial is None or lote_diario.peso_medio_inicial <= 0:
        return {'error': 'Peso médio inicial do dia é inválido.'}

    peso_base_g = lote_diario.peso_medio_inicial
    detalhe_curva = get_detalhe_curva_para_peso(lote.curva_crescimento, peso_base_g)
    
    logging.info(f"[SUGESTÃO] Lote {lote.id}: Peso base do dia: {peso_base_g}g. Detalhe curva: {detalhe_curva}")

    if not detalhe_curva:
        return {'error': f'Nenhum ponto na curva para o peso de {peso_base_g}g.'}

    percentual_pv = detalhe_curva.arracoamento_biomassa_perc
    produto_racao = detalhe_curva.racao

    if not percentual_pv or percentual_pv <= 0:
        return {'error': f'Ponto da curva para {peso_base_g}g sem % arraçoamento.'}
    if not produto_racao:
        return {'error': f'Ponto da curva para {peso_base_g}g sem ração definida.'}

    # Usa a biomassa inicial do dia, que já foi calculada corretamente.
    biomassa_kg = lote_diario.biomassa_inicial
    quantidade_sugerida_kg = calc_racao_kg(biomassa_kg, percentual_pv)
    
    logging.info(f"[SUGESTÃO] Lote {lote.id}: Biomassa inicial do dia: {biomassa_kg}kg, Ração Sugerida: {quantidade_sugerida_kg}kg")

    return {
        'lote': lote,
        'produto_racao': produto_racao,
        'quantidade_kg': quantidade_sugerida_kg,
        'biomassa_kg': biomassa_kg,
        'percentual_pv': percentual_pv
    }


def reprojetar_ciclo_de_vida(lote: Lote, data_de_inicio: date, quantidade_base_override: Decimal = None, peso_base_g_override: Decimal = None, ultimo_ld_override: LoteDiario = None):
    """
    Recalcula a projeção de vida de um lote a partir de uma data, usando o último estado conhecido.
    Pode receber quantidade_base_override e peso_base_g_override para forçar o ponto de partida.
    Pode receber ultimo_ld_override para forçar o LoteDiario do dia anterior.
    """
    if not lote.curva_crescimento:
        return

    # Encontra o último estado conhecido (dia anterior ao início da reprojeção)
    # Usa o override se fornecido, caso contrário, busca no banco de dados.
    ultimo_ld = ultimo_ld_override
    if not ultimo_ld and (quantidade_base_override is None or peso_base_g_override is None):
        ultimo_ld = LoteDiario.objects.filter(
            lote=lote,
            data_evento__lt=data_de_inicio
        ).order_by('-data_evento').first()

    if ultimo_ld:
        # Garante que o ultimo_ld está com os dados reais mais recentes antes de usá-lo como base.
        recalcular_lote_diario_real(ultimo_ld, commit=True)

        # RECARREGA o objeto do banco de dados para garantir que temos os dados mais frescos
        # após o recálculo, evitando problemas com objetos 'stale' em memória.
        ultimo_ld.refresh_from_db()

        # A base mais precisa é o dado real. Se não existir, usa o projetado do dia anterior.
        peso_base_g = ultimo_ld.peso_medio_real if ultimo_ld.peso_medio_real is not None else ultimo_ld.peso_medio_projetado
        quantidade_base = ultimo_ld.quantidade_real if ultimo_ld.quantidade_real is not None else ultimo_ld.quantidade_projetada
    else:
        # Se não há histórico, usa os dados iniciais do próprio lote.
        peso_base_g = lote.peso_medio_inicial
        quantidade_base = lote.quantidade_inicial

    # Aplica os overrides se fornecidos, garantindo que a reprojeção comece do ponto desejado.
    if quantidade_base_override is not None:
        quantidade_base = quantidade_base_override
    if peso_base_g_override is not None:
        peso_base_g = peso_base_g_override
    
    # Fallback final para garantir que as bases não sejam nulas.
    if peso_base_g is None: peso_base_g = lote.peso_medio_inicial
    if quantidade_base is None: quantidade_base = lote.quantidade_inicial

    logging.debug(f"DEBUG REPROJETAR: Após overrides/fallback - quantidade_base: {quantidade_base}, peso_base_g: {peso_base_g}")
    
    qs = LoteDiario.objects.filter(lote=lote, data_evento__gte=data_de_inicio)

    # apaga SOMENTE projetados (sem real)
    qs.filter(
        racao_realizada_kg__isnull=True,
        peso_medio_real__isnull=True,
        usuario_lancamento__isnull=True
    ).delete()

    # Pega as datas que já existem para não sobrescrevê-las
    # REMOVIDO: datas_existentes = set(LoteDiario.objects.filter(lote=lote, data_evento__gte=data_de_inicio).values_list('data_evento', flat=True))

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

    logging.debug(f"DEBUG REPROJETAR: Início do loop - data_corrente: {data_corrente}, quantidade_projetada_corrente: {quantidade_projetada_corrente}, peso_corrente_g: {peso_corrente_g}")

    # REMOVIDO: registros_lote_diario = []

    for detalhe in detalhes_para_projetar:
        if detalhe.periodo_dias <= 0: continue

        mortalidade_diaria_perc = q3(detalhe.mortalidade_presumida_perc / Decimal(detalhe.periodo_dias) if detalhe.periodo_dias > 0 else Decimal('0'))

        for _ in range(detalhe.periodo_dias):
            logging.debug(f"DEBUG REPROJETAR: Dentro do loop diário - data: {data_corrente}, Qtd Proj Corrente: {quantidade_projetada_corrente}, Peso Proj Corrente: {peso_corrente_g}")
            # --- MODIFIED LOGIC: Tenta obter ou cria o LoteDiario e atualiza campos projetados ---
            # Não pula mais a criação/atualização se a data já existe.
            # Apenas atualiza os campos projetados do registro existente.
            
            # CÁLCULOS PADRONIZADOS
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
            
            # CORREÇÃO: Apura eventos de manejo que ocorreram no dia (entradas/saídas)
            # e ajusta a quantidade projetada para refletir a realidade do dia antes de salvar.
            # Isso torna a projeção "inteligente" a eventos históricos.
            eventos_do_dia = EventoManejo.objects.filter(lote=lote, data_evento=data_corrente)

            for ev in eventos_do_dia:
                q = (ev.quantidade or Decimal('0'))
                t = ev.tipo_evento.nome.lower() if ev.tipo_evento else ''
                mov = (ev.tipo_movimento or '').lower()

                # ✅ não duplicar povoamento do dia inicial (já está no lote.quantidade_inicial)
                if data_corrente == lote.data_povoamento and t == 'povoamento':
                    continue

                # ENTRADAS que afetam estoque
                if mov == 'entrada' and t in ('povoamento', 'classificacao', 'transferencia'):
                    quantidade_final_dia += q

                # SAÍDAS que afetam estoque
                elif mov in ('saida', 'saída') and t in ('mortalidade', 'despesca', 'transferencia'):
                    quantidade_final_dia -= q

            biomassa_final_dia_kg = calc_biomassa_kg(quantidade_final_dia, peso_final_dia_g)
            gpt_projetado_valor_g = peso_final_dia_g - lote.peso_medio_inicial
            # FIM CÁLCULOS PADRONIZADOS

            ld_obj, created = LoteDiario.objects.get_or_create(
                lote=lote,
                data_evento=data_corrente,
                defaults={
                    'tanque': lote.tanque_atual,
                    'quantidade_inicial': quantidade_projetada_corrente,
                    'peso_medio_inicial': peso_corrente_g,
                    'biomassa_inicial': biomassa_inicio_dia_kg,
                    'quantidade_projetada': quantidade_final_dia,
                    'peso_medio_projetado': peso_final_dia_g,
                    'biomassa_projetada': biomassa_final_dia_kg,
                    'gpd_projetado': gpd_calculado_g,
                    'gpt_projetado': gpt_projetado_valor_g,
                    'racao_sugerida': detalhe.racao,
                    'racao_sugerida_kg': racao_sugerida_kg,
                    'conversao_alimentar_projetada': tca_da_curva
                }
            )

            # Se o objeto já existia, atualiza os campos projetados.
            if not created:
                ld_obj.tanque = lote.tanque_atual
                ld_obj.quantidade_inicial = quantidade_projetada_corrente
                ld_obj.peso_medio_inicial = peso_corrente_g
                ld_obj.biomassa_inicial = biomassa_inicio_dia_kg
                ld_obj.quantidade_projetada = quantidade_final_dia
                ld_obj.peso_medio_projetado = peso_final_dia_g
                ld_obj.biomassa_projetada = biomassa_final_dia_kg
                ld_obj.gpd_projetado = gpd_calculado_g
                ld_obj.gpt_projetado = gpt_projetado_valor_g
                ld_obj.racao_sugerida = detalhe.racao
                ld_obj.racao_sugerida_kg = racao_sugerida_kg
                ld_obj.conversao_alimentar_projetada = tca_da_curva
                ld_obj.save(update_fields=[
                    'tanque', 'quantidade_inicial', 'peso_medio_inicial', 'biomassa_inicial',
                    'quantidade_projetada', 'peso_medio_projetado', 'biomassa_projetada',
                    'gpd_projetado', 'gpt_projetado', 'racao_sugerida', 'racao_sugerida_kg',
                    'conversao_alimentar_projetada'
                ])
            logging.debug(f"DEBUG REPROJETAR: Após save/update - data: {data_corrente}, Qtd Proj Salva: {ld_obj.quantidade_projetada}, Peso Proj Salvo: {ld_obj.peso_medio_projetado}")
            # --- FIM MODIFIED LOGIC ---

            peso_corrente_g = peso_final_dia_g
            quantidade_projetada_corrente = quantidade_final_dia
            data_corrente += timedelta(days=1)
    
    # REMOVIDO: if registros_lote_diario: LoteDiario.objects.bulk_create(registros_lote_diario)

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
        # CORREÇÃO: Acessa o atributo .nome do objeto ForeignKey
        t = ev.tipo_evento.nome.lower() if ev.tipo_evento else ''
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


def _clamp_decimal(x, mn, mx):
    if x is None:
        return None
    if x < mn:
        return mn
    if x > mx:
        return mx
    return x


def fator_resposta_biologica(p: Decimal) -> Decimal:
    """
    Função não-linear de resposta de crescimento ao % da ração.
    p = racao_real / racao_base (base = sugerida_ajustada ou sugerida)

    Fórmula: 2p / (1+p)
    - Saturação para p > 1
    - Queda acelerada para p < 1

    Clamp aplicado para evitar projeções irreais:
      min 0.50 (restrição forte)
      max 1.05 (acima de 110% quase não cresce mais na prática)
    """
    if p <= Decimal('0'):
        return Decimal('0.50')

    f = (Decimal('2.0') * p) / (Decimal('1.0') + p)
    return _clamp_decimal(f, Decimal('0.50'), Decimal('1.05'))


def obter_base_sugerida(ld: LoteDiario) -> Decimal:
    """
    Base para comparação e cálculo:
    - se existir sugerida ajustada: usa ela
    - senão: usa sugerida base
    """
    if ld.racao_sugerida_ajustada_kg is not None and ld.racao_sugerida_ajustada_kg > 0:
        return Decimal(ld.racao_sugerida_ajustada_kg)
    if ld.racao_sugerida_kg is not None and ld.racao_sugerida_kg > 0:
        return Decimal(ld.racao_sugerida_kg)
    return Decimal('0')


from django.db.models import Sum
from django.utils import timezone
from .models import ArracoamentoRealizado, LoteDiario # LoteDiario already imported, but explicit for clarity


def recalcular_lote_diario_real(ld: LoteDiario, user=None, commit=True):
    """
    Recalcula todas as métricas reais de um LoteDiario com base nos ArracoamentoRealizado do dia.
    Esta é a fonte única de verdade para o cálculo do FCR não-linear.
    O parâmetro 'commit' controla se as alterações são salvas no banco.
    """
    # --- Correção 3.2 & 4.B: Hardening e consistência ---

    # Garante que a FK da ração está setada, usando o último lançamento como fonte da verdade.
    ultimo_real = ld.realizacoes.order_by("-data_realizacao", "-data_lancamento").first()
    ld.racao_realizada = ultimo_real.produto_racao if ultimo_real and getattr(ultimo_real, 'produto_racao_id', None) else None

    # Garante que a quantidade real do dia está apurada, caso ainda não esteja.
    if ld.quantidade_real is None:
        ld.quantidade_real = _apurar_quantidade_real_no_dia(ld)

    # 1. racao_realizada_kg = soma das realizações do dia
    total_real_do_dia = ld.realizacoes.aggregate(s=Sum('quantidade_kg'))['s'] or Decimal('0')
    ld.racao_realizada_kg = total_real_do_dia

    # 2. base_sugerida = ajustada se existir senão base
    base_sugerida = obter_base_sugerida(ld)

    # 3. p = real/base
    p = total_real_do_dia / base_sugerida if base_sugerida > 0 else Decimal('0')

    # 4. f = 2p/(1+p) com clamp
    fator_crescimento = fator_resposta_biologica(p)

    # 5. Evita "mismatch" no ganho ideal, recalculando com base na quantidade consistente.
    qtd = Decimal(ld.quantidade_real or ld.quantidade_inicial or 0)

    # Busca o peso médio real do dia anterior para usar como base para o cálculo do crescimento.
    ld_anterior = LoteDiario.objects.filter(lote=ld.lote, data_evento=ld.data_evento - timedelta(days=1)).first()
    if ld_anterior and ld_anterior.peso_medio_real is not None:
        peso_ini_real_do_dia = ld_anterior.peso_medio_real
    else:
        # Se não há dia anterior ou peso real, usa o peso médio inicial do lote como fallback.
        peso_ini_real_do_dia = ld.lote.peso_medio_inicial

    # O peso projetado para o final do dia, usando o peso inicial real como fallback.
    # peso_proj = Decimal(ld.peso_medio_projetado or peso_ini_real_do_dia) # Removido, não será mais usado diretamente aqui

    # --- NOVO CÁLCULO PARA ganho_ideal_total_kg ---
    # Calcula o ganho ideal com base na curva de crescimento para o peso real atual,
    # tornando-o independente dos valores projetados do LoteDiario.
    curva = ld.lote.curva_crescimento
    ganho_ideal_total_kg = Decimal('0')
    if curva:
        detalhe_curva = get_detalhe_curva_para_peso(curva, peso_ini_real_do_dia)
        if detalhe_curva and detalhe_curva.gpd > 0:
            gpd_ideal_g = detalhe_curva.gpd # GPD da curva é por peixe
            ganho_ideal_total_kg = (gpd_ideal_g * qtd) / Decimal('1000') # Converte para kg total
    # --- FIM NOVO CÁLCULO ---

    # Old lines (removidas):
    # biom_ini = calc_biomassa_kg(qtd, peso_ini_real_do_dia)
    # biom_proj = calc_biomassa_kg(qtd, peso_proj)
    # ganho_ideal_total_kg = max(Decimal('0'), biom_proj - biom_ini)

    # 6. ganho_real_total_kg = ganho_ideal_total_kg * f
    ganho_real_total_kg = (ganho_ideal_total_kg * fator_crescimento) if ganho_ideal_total_kg > 0 else Decimal('0')

    # 7. peso_medio_real = peso_medio_inicial + (ganho_real_total_kg*1000 / quantidade)
    if qtd > 0:
        ganho_real_por_peixe_g = (ganho_real_total_kg * Decimal('1000')) / qtd
        ld.peso_medio_real = peso_ini_real_do_dia + ganho_real_por_peixe_g
        ld.gpd_real = ganho_real_por_peixe_g
    else:
        ld.peso_medio_real = peso_ini_real_do_dia # Mantém o peso do dia anterior se não houver peixes
        ld.gpd_real = Decimal('0')

    # 8. biomassa_real = quantidade * peso_medio_real / 1000
    ld.biomassa_real = calc_biomassa_kg(qtd, ld.peso_medio_real)

    # 9. FCR_real = real / ganho_real com trava de mínimo
    if ganho_real_total_kg > Decimal('0.001'):
        ld.conversao_alimentar_real = total_real_do_dia / ganho_real_total_kg
    else:
        ld.conversao_alimentar_real = None

    # GPT (ganho por peixe no período do dia) = peso_final - peso_inicial
    ld.gpt_real = (Decimal(ld.peso_medio_real or 0) - peso_ini_real_do_dia)

    # Atualiza usuário e timestamps
    if user:
        if not ld.usuario_lancamento: # Só atribui se não houver um
            ld.usuario_lancamento = user
        ld.usuario_edicao = user
        ld.data_edicao = timezone.now()

    # Salva todas as alterações no LoteDiario, incluindo os campos de base para consistência.
    if commit:
        ld.save(update_fields=[
            'racao_realizada',
            'racao_realizada_kg',
            'conversao_alimentar_real',
            'peso_medio_real',
            'gpd_real',
            'biomassa_real',
            'gpt_real',
            'quantidade_real',
            'quantidade_inicial',
            'peso_medio_inicial',
            'biomassa_inicial',
            'usuario_lancamento',
            'usuario_edicao',
            'data_edicao'
        ])


from .models import ParametroAmbientalDiario # Import needed for calcular_fator_ambiente


def fator_od(od_mg_l: Decimal | None) -> Decimal:
    """
    Fator por oxigênio dissolvido (mg/L).
    Regras simples e seguras (tilápia):
    - >= 5.0: 1.00
    - 4.0–4.99: 0.95
    - 3.0–3.99: 0.85
    - 2.0–2.99: 0.70
    - < 2.0: 0.50
    """
    if od_mg_l is None:
        return Decimal('1.00')

    od = Decimal(od_mg_l)
    if od >= Decimal('5.0'):
        return Decimal('1.00')
    if od >= Decimal('4.0'):
        return Decimal('0.95')
    if od >= Decimal('3.0'):
        return Decimal('0.85')
    if od >= Decimal('2.0'):
        return Decimal('0.70')
    return Decimal('0.50')


def fator_temp(temp_c: Decimal | None) -> Decimal:
    """
    Fator por temperatura (°C).
    Regras simples e seguras (tilápia):
    - 26–30: 1.00 (faixa ótima)
    - 24–25.99 ou 30.01–32: 0.95
    - 22–23.99 ou 32.01–34: 0.85
    - 20–21.99 ou 34.01–36: 0.70
    - fora disso: 0.50
    """
    if temp_c is None:
        return Decimal('1.00')

    t = Decimal(temp_c)
    if Decimal('26.0') <= t <= Decimal('30.0'):
        return Decimal('1.00')
    if Decimal('24.0') <= t < Decimal('26.0') or Decimal('30.0') < t <= Decimal('32.0'):
        return Decimal('0.95')
    if Decimal('22.0') <= t < Decimal('24.0') or Decimal('32.0') < t <= Decimal('34.0'):
        return Decimal('0.85')
    if Decimal('20.0') <= t < Decimal('22.0') or Decimal('34.0') < t <= Decimal('36.0'):
        return Decimal('0.70')
    return Decimal('0.50')


def calcular_fator_ambiente(param_amb) -> dict:
    """
    Retorna snapshot de ambiente + fator_ambiente (clamp 0.50–1.10).
    param_amb é ParametroAmbientalDiario (ou None).
    """
    if not param_amb:
        return {
            'od_medio': None,
            'temp_media': None,
            'temp_min': None,
            'temp_max': None,
            'variacao_termica': None,
            'fator_do': Decimal('1.00'),
            'fator_temp': Decimal('1.00'),
            'fator_ambiente': Decimal('1.00'),
        }

    od_medio = getattr(param_amb, 'od_medio', None)
    temp_media = getattr(param_amb, 'temp_media', None)

    f_do = fator_od(od_medio)
    f_t = fator_temp(temp_media)

    fator = f_do * f_t
    fator = _clamp_decimal(fator, Decimal('0.50'), Decimal('1.10'))

    return {
        'od_medio': od_medio,
        'temp_media': temp_media,
        'temp_min': getattr(param_amb, 'temp_min', None),
        'temp_max': getattr(param_amb, 'temp_max', None),
        'variacao_termica': getattr(param_amb, 'variacao_termica', None),
        'fator_do': f_do,
        'fator_temp': f_t,
        'fator_ambiente': fator,
    }