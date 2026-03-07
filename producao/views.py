import json
import logging
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q, Sum, Case, When, F, Value
from django.db.models.fields import DecimalField
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.utils import timezone
import pandas as pd
from io import BytesIO
from datetime import datetime, time, date, timedelta
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods, require_POST

from .models import Lote, Tanque, LoteDiario  # ajuste nomes exatos
from .views_arracoamento import recalcular_lote_diario_real, reprojetar_ciclo_de_vida, _apurar_quantidade_real_no_dia
from .utils import calc_biomassa_kg, obter_tanque_lote_em_data, construir_resolvedor_tanque_lote  # ajuste


from .models import (
    Tanque, CurvaCrescimento, CurvaCrescimentoDetalhe, Lote, 
    EventoManejo, Unidade, Malha, TipoTela, TipoEvento,
    FaseProducao, TipoTanque, LinhaProducao, StatusTanque, Atividade, LoteDiario
)
from .forms import (
    TanqueForm, CurvaCrescimentoForm, CurvaCrescimentoDetalheForm, ImportarCurvaForm, LoteForm, 
    EventoManejoForm, TanqueImportForm,
    UnidadeForm, MalhaForm, TipoTelaForm, LinhaProducaoForm, FaseProducaoForm,
    StatusTanqueForm, TipoTanqueForm, TipoEventoForm, AtividadeForm, PovoamentoForm
)
from .utils import AjaxFormMixin, BulkDeleteView
from common.utils import render_ajax_or_base
from common.messages_utils import get_app_messages
from produto.models import Produto

# === Views de Suporte ===

class UnidadeListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Unidade
    template_name = 'producao/suporte/unidade_list.html'
    permission_required = 'producao.view_unidade'

class UnidadeCreateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = Unidade
    form_class = UnidadeForm
    template_name = 'producao/suporte/unidade_form.html'
    success_url = reverse_lazy('producao:lista_unidades')
    permission_required = 'producao.add_unidade'

class UnidadeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = Unidade
    form_class = UnidadeForm
    template_name = 'producao/suporte/unidade_form.html'
    success_url = reverse_lazy('producao:lista_unidades')
    permission_required = 'producao.change_unidade'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['data_page'] = 'editar_unidade'
        context['data_tela'] = 'editar_unidade'
        return context

class MalhaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Malha
    template_name = 'producao/suporte/malha_list.html'
    permission_required = 'producao.view_malha'

class MalhaCreateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = Malha
    form_class = MalhaForm
    template_name = 'producao/suporte/malha_form.html'
    success_url = reverse_lazy('producao:lista_malhas')
    permission_required = 'producao.add_malha'

class MalhaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = Malha
    form_class = MalhaForm
    template_name = 'producao/suporte/malha_form.html'
    success_url = reverse_lazy('producao:lista_malhas')
    permission_required = 'producao.change_malha'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['data_page'] = 'editar_malha'
        context['data_tela'] = 'editar_malha'
        return context

class TipoTelaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = TipoTela
    template_name = 'producao/suporte/tipotela_list.html'
    permission_required = 'producao.view_tipotela'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['data_page'] = 'lista_tipotelas'
        context['data_tela'] = 'lista_tipotelas'
        return context

    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)

class TipoTelaCreateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = TipoTela
    form_class = TipoTelaForm
    template_name = 'producao/suporte/tipotela_form.html'
    success_url = reverse_lazy('producao:lista_tipotelas')
    permission_required = 'producao.add_tipotela'

class TipoTelaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = TipoTela
    form_class = TipoTelaForm
    template_name = 'producao/suporte/tipotela_form.html'
    success_url = reverse_lazy('producao:lista_tipotelas')
    permission_required = 'producao.change_tipotela'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['data_page'] = 'editar_tipotela'
        context['data_tela'] = 'editar_tipotela'
        return context

class ExcluirUnidadesMultiplosView(BulkDeleteView):
    model = Unidade
    permission_required = 'producao.delete_unidade'
    success_url_name = 'producao:lista_unidades'

class ExcluirMalhasMultiplosView(BulkDeleteView):
    model = Malha
    permission_required = 'producao.delete_malha'
    success_url_name = 'producao:lista_malhas'

class ExcluirTiposTelaMultiplosView(BulkDeleteView):
    model = TipoTela
    permission_required = 'producao.delete_tipotela'
    success_url_name = 'producao:lista_tipotelas'


# Linha de Produção
class LinhaProducaoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = LinhaProducao
    template_name = 'producao/suporte/linhaproducao_list.html'
    permission_required = 'producao.view_linhaproducao'

    def render_to_response(self, context, **response_kwargs):
        context['data_page'] = 'lista_linhasproducao'
        context['data_tela'] = 'lista_linhasproducao'
        return render_ajax_or_base(self.request, self.template_name, context)

class LinhaProducaoCreateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = LinhaProducao
    form_class = LinhaProducaoForm
    template_name = 'producao/suporte/linhaproducao_form.html'
    success_url = reverse_lazy('producao:lista_linhasproducao')
    permission_required = 'producao.add_linhaproducao'

    def render_to_response(self, context, **response_kwargs):
        context['data_page'] = 'criar_linhaproducao'
        context['data_tela'] = 'criar_linhaproducao'
        return render_ajax_or_base(self.request, self.template_name, context)

class LinhaProducaoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = LinhaProducao
    form_class = LinhaProducaoForm
    template_name = 'producao/suporte/linhaproducao_form.html'
    success_url = reverse_lazy('producao:lista_linhasproducao')
    permission_required = 'producao.change_linhaproducao'

    def render_to_response(self, context, **response_kwargs):
        context['data_page'] = 'editar_linhaproducao'
        context['data_tela'] = 'editar_linhaproducao'
        return render_ajax_or_base(self.request, self.template_name, context)

# Fase de Produção
class FaseProducaoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = FaseProducao
    template_name = 'producao/suporte/faseproducao_list.html'
    permission_required = 'producao.view_faseproducao'

    def render_to_response(self, context, **response_kwargs):
        context['data_page'] = 'lista_fasesproducao'
        context['data_tela'] = 'lista_fasesproducao'
        return render_ajax_or_base(self.request, self.template_name, context)

class FaseProducaoCreateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = FaseProducao
    form_class = FaseProducaoForm
    template_name = 'producao/suporte/faseproducao_form.html'
    success_url = reverse_lazy('producao:lista_fasesproducao')
    permission_required = 'producao.add_faseproducao'

    def render_to_response(self, context, **response_kwargs):
        context['data_page'] = 'criar_faseproducao'
        context['data_tela'] = 'criar_faseproducao'
        return render_ajax_or_base(self.request, self.template_name, context)

class FaseProducaoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = FaseProducao
    form_class = FaseProducaoForm
    template_name = 'producao/suporte/faseproducao_form.html'
    success_url = reverse_lazy('producao:lista_fasesproducao')
    permission_required = 'producao.change_faseproducao'

    def render_to_response(self, context, **response_kwargs):
        context['data_page'] = 'editar_faseproducao'
        context['data_tela'] = 'editar_faseproducao'
        return render_ajax_or_base(self.request, self.template_name, context)

# Status do Tanque
class StatusTanqueListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = StatusTanque
    template_name = 'producao/suporte/statustanque_list.html'
    permission_required = 'producao.view_statustanque'

    def render_to_response(self, context, **response_kwargs):
        context['data_page'] = 'lista_statustanque'
        context['data_tela'] = 'lista_statustanque'
        return render_ajax_or_base(self.request, self.template_name, context)

class StatusTanqueCreateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = StatusTanque
    form_class = StatusTanqueForm
    template_name = 'producao/suporte/statustanque_form.html'
    success_url = reverse_lazy('producao:lista_statustanque')
    permission_required = 'producao.add_statustanque'

    def render_to_response(self, context, **response_kwargs):
        context['data_page'] = 'criar_statustanque'
        context['data_tela'] = 'criar_statustanque'
        return render_ajax_or_base(self.request, self.template_name, context)

class StatusTanqueUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = StatusTanque
    form_class = StatusTanqueForm
    template_name = 'producao/suporte/statustanque_form.html'
    success_url = reverse_lazy('producao:lista_statustanque')
    permission_required = 'producao.change_statustanque'

    def render_to_response(self, context, **response_kwargs):
        context['data_page'] = 'editar_statustanque'
        context['data_tela'] = 'editar_statustanque'
        return render_ajax_or_base(self.request, self.template_name, context)

# Tipo de Tanque
class TipoTanqueListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = TipoTanque
    template_name = 'producao/suporte/tipotanque_list.html'
    permission_required = 'producao.view_tipotanque'

    def render_to_response(self, context, **response_kwargs):
        context['data_page'] = 'lista_tipostanque'
        context['data_tela'] = 'lista_tipostanque'
        return render_ajax_or_base(self.request, self.template_name, context)

class TipoTanqueCreateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = TipoTanque
    form_class = TipoTanqueForm
    template_name = 'producao/suporte/tipotanque_form.html'
    success_url = reverse_lazy('producao:lista_tipostanque')
    permission_required = 'producao.add_tipotanque'

    def render_to_response(self, context, **response_kwargs):
        context['data_page'] = 'criar_tipotanque'
        context['data_tela'] = 'criar_tipotanque'
        return render_ajax_or_base(self.request, self.template_name, context)

class TipoTanqueUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = TipoTanque
    form_class = TipoTanqueForm
    template_name = 'producao/suporte/tipotanque_form.html'
    success_url = reverse_lazy('producao:lista_tipostanque')
    permission_required = 'producao.change_tipotanque'

    def render_to_response(self, context, **response_kwargs):
        context['data_page'] = 'editar_tipotanque'
        context['data_tela'] = 'editar_tipotanque'
        return render_ajax_or_base(self.request, self.template_name, context)


# Tipo de Evento
class TipoEventoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = TipoEvento
    template_name = 'producao/suporte/tipoevento_list.html'
    permission_required = 'producao.view_tipoevento'

    def render_to_response(self, context, **response_kwargs):
        context['data_page'] = 'lista_tiposevento'
        context['data_tela'] = 'lista_tiposevento'
        return render_ajax_or_base(self.request, self.template_name, context)

class TipoEventoCreateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = TipoEvento
    form_class = TipoEventoForm
    template_name = 'producao/suporte/tipoevento_form.html'
    success_url = reverse_lazy('producao:lista_tiposevento')
    permission_required = 'producao.add_tipoevento'

    def render_to_response(self, context, **response_kwargs):
        context['data_page'] = 'criar_tipoevento'
        context['data_tela'] = 'criar_tipoevento'
        return render_ajax_or_base(self.request, self.template_name, context)

class TipoEventoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = TipoEvento
    form_class = TipoEventoForm
    template_name = 'producao/suporte/tipoevento_form.html'
    success_url = reverse_lazy('producao:lista_tiposevento')
    permission_required = 'producao.change_tipoevento'

    def render_to_response(self, context, **response_kwargs):
        context['data_page'] = 'editar_tipoevento'
        context['data_tela'] = 'editar_tipoevento'
        return render_ajax_or_base(self.request, self.template_name, context)

# Atividade
# === Tanques ===

class ListaTanquesView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Tanque
    template_name = 'producao/tanques/lista_tanques.html'
    context_object_name = 'tanques'
    permission_required = 'producao.view_tanque'
    raise_exception = True

    def get_queryset(self):
        qs = super().get_queryset()
        termo = self.request.GET.get('termo_tanque', '').strip()
        if termo:
            qs = qs.filter(
                Q(nome__icontains=termo) |
                Q(tag_tanque__icontains=termo) |
                Q(unidade__nome__icontains=termo) |
                Q(linha_producao__nome__icontains=termo) |
                Q(tipo_tanque__nome__icontains=termo) |
                Q(status_tanque__nome__icontains=termo)
            )
        return qs.select_related('unidade', 'linha_producao', 'fase', 'tipo_tanque', 'status_tanque')

    def render_to_response(self, context, **response_kwargs):
        context['termo_busca'] = self.request.GET.get('termo_tanque', '').strip()
        context['data_page'] = 'lista_tanques'
        context['data_tela'] = 'lista_tanques'
        return render_ajax_or_base(self.request, self.template_name, context)


class CadastrarTanqueView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = Tanque
    form_class = TanqueForm
    template_name = 'producao/tanques/cadastrar_tanque.html'
    success_url = reverse_lazy('producao:lista_tanques')
    permission_required = 'producao.add_tanque'
    raise_exception = True

    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)


class EditarTanqueView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = Tanque
    form_class = TanqueForm
    template_name = 'producao/tanques/editar_tanque.html'
    success_url = reverse_lazy('producao:lista_tanques')
    permission_required = 'producao.change_tanque'
    raise_exception = True

    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)


class ExcluirTanquesMultiplosView(BulkDeleteView):
    model = Tanque
    permission_required = 'producao.delete_tanque'
    success_url_name = 'producao:lista_tanques'

@login_required
@permission_required('producao.add_tanque', raise_exception=True)
def importar_tanques_view(request):
    from decimal import Decimal
    app_messages = get_app_messages(request)
    template = 'producao/tanques/importar_tanques.html'
    redirect_url = reverse('producao:lista_tanques')

    if request.method == 'POST':
        form = TanqueImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                df = pd.read_excel(request.FILES['arquivo_excel'])
                df.columns = [c.strip().lower() for c in df.columns]

                required_cols = ['nome', 'unidade', 'linha_producao', 'fase', 'tipo_tanque',
                                 'status_tanque', 'malha']
                if not all(col in df.columns for col in required_cols):
                    raise ValueError("Colunas obrigatórias não encontradas. Verifique o template.")

                created_count = 0
                updated_count = 0

                with transaction.atomic():
                    for index, row in df.iterrows():
                        # --- Função auxiliar para tratar FKs ---
                        def get_fk_object(model, nome_valor):
                            if pd.notna(nome_valor) and str(nome_valor).strip():
                                obj, _ = model.objects.get_or_create(nome__iexact=str(nome_valor).strip(), defaults={'nome': str(nome_valor).strip()})
                                return obj
                            return None

                        # --- Trata FKs, prevenindo criação de "nan" ---
                        unidade = get_fk_object(Unidade, row.get('unidade'))
                        linha = get_fk_object(LinhaProducao, row.get('linha_producao'))
                        fase = get_fk_object(FaseProducao, row.get('fase'))
                        tipo = get_fk_object(TipoTanque, row.get('tipo_tanque'))
                        status = get_fk_object(StatusTanque, row.get('status_tanque'))
                        malha = get_fk_object(Malha, row.get('malha'))

                        # --- Trata campos numéricos, convertendo NaN para None ---
                        largura_val = _to_decimal(row.get('largura')) if pd.notna(row.get('largura')) else None
                        comprimento_val = _to_decimal(row.get('comprimento')) if pd.notna(row.get('comprimento')) else None
                        profundidade_val = _to_decimal(row.get('profundidade')) if pd.notna(row.get('profundidade')) else None
                        sequencia_val = int(row['sequencia']) if pd.notna(row.get('sequencia')) else None

                        # --- Trata campo de texto, convertendo NaN para string vazia ---
                        tag_val = str(row.get('tag_tanque', '')).strip() if pd.notna(row.get('tag_tanque')) else ''

                        # --- Recalcula campos dimensionais ---
                        mq = None
                        mc = None
                        ha = None
                        if largura_val is not None and comprimento_val is not None:
                            mq = largura_val * comprimento_val
                        if mq is not None and profundidade_val is not None:
                            mc = mq * profundidade_val
                        if mq is not None:
                            ha = mq / Decimal("10000")

                        # --- Atualiza ou cria o tanque com valores limpos ---
                        tanque, created = Tanque.objects.update_or_create(
                            nome=row['nome'],
                            defaults={
                                'unidade': unidade,
                                'linha_producao': linha,
                                'fase': fase,
                                'tipo_tanque': tipo,
                                'status_tanque': status,
                                'malha': malha,
                                'largura': largura_val,
                                'comprimento': comprimento_val,
                                'profundidade': profundidade_val,
                                'sequencia': sequencia_val,
                                'tag_tanque': tag_val,
                                'metro_quadrado': mq,
                                'metro_cubico': mc,
                                'ha': ha,
                            }
                        )
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1

                message = f"Importação concluída: {created_count} tanques criados, {updated_count} tanques atualizados."
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': message, 'redirect_url': redirect_url})
                return redirect(redirect_url)

            except Exception as e:
                error_message = f"Ocorreu um erro ao processar o arquivo: {e}"
                app_messages.error(error_message)
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': error_message}, status=400)
                return render(request, template, {'form': form})
    else:
        form = TanqueImportForm()

    return render_ajax_or_base(request, template, {'form': form})

def _to_decimal(s):
    if s is None:
        return None
    val = str(s).strip()
    if not val:
        return None
    
    # Detecta se o formato é brasileiro (ex: "1.234,56")
    # A heurística é a presença de vírgula como último separador.
    last_comma = val.rfind(',')
    last_dot = val.rfind('.')
    
    if last_comma > last_dot:
        # Formato brasileiro: "1.234,56" -> "1234.56"
        val = val.replace('.', '').replace(',', '.')
    # Se for formato americano ("1,234.56"), removemos apenas a vírgula
    elif last_dot > last_comma:
        val = val.replace(',', '')
        
    try:
        return Decimal(val)
    except InvalidOperation:
        return None

@login_required
@permission_required('producao.view_tanque', raise_exception=True)
def download_template_tanque_view(request):
    headers = [
        'nome', 'largura', 'profundidade', 'comprimento', 'unidade', 'fase',
        'tipo_tanque', 'linha_producao', 'sequencia', 'malha', 'status_tanque', 'tag_tanque'
    ]
    df = pd.DataFrame(columns=headers)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Template Tanques')
    output.seek(0)
    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="template_tanques.xlsx"'
    return response

# === Curvas de Crescimento ===

class ListaCurvasView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = CurvaCrescimento
    template_name = 'producao/curvas/lista_curvas.html'
    context_object_name = 'curvas'
    permission_required = 'producao.view_curvacrescimento'
    raise_exception = True

    def get_queryset(self):
        qs = super().get_queryset()
        termo = self.request.GET.get('termo_curva', '').strip()
        if termo:
            qs = qs.filter(Q(nome__icontains=termo) | Q(especie__icontains=termo))
        return qs

    def render_to_response(self, context, **response_kwargs):
        context['termo_busca'] = self.request.GET.get('termo_curva', '').strip()
        return render_ajax_or_base(self.request, self.template_name, context)


class CadastrarCurvaView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = CurvaCrescimento
    form_class = CurvaCrescimentoForm
    template_name = 'producao/curvas/cadastrar_curva.html'
    success_url = reverse_lazy('producao:lista_curvas')
    permission_required = 'producao.add_curvacrescimento'
    raise_exception = True

    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)


class EditarCurvaView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = CurvaCrescimento
    form_class = CurvaCrescimentoForm
    template_name = 'producao/curvas/editar_curva.html'
    success_url = reverse_lazy('producao:lista_curvas')
    permission_required = 'producao.change_curvacrescimento'
    raise_exception = True

    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)


class DetalheCurvaView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = CurvaCrescimento
    template_name = 'producao/curvas/detalhe_curva.html'
    context_object_name = 'curva'
    permission_required = 'producao.view_curvacrescimento'
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['detalhes'] = CurvaCrescimentoDetalhe.objects.filter(curva=self.object).order_by('periodo_semana')
        return context

    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)


class ExcluirCurvasMultiplasView(BulkDeleteView):
    model = CurvaCrescimento
    permission_required = 'producao.delete_curvacrescimento'
    success_url_name = 'producao:lista_curvas'


# --- Views Funcionais para Curva (Lógica Customizada) ---

@login_required
@permission_required('producao.add_curvacrescimento', raise_exception=True)
def importar_curva_view(request):
    app_messages = get_app_messages(request)
    template = 'producao/curvas/importar_curva.html'
    redirect_url = reverse('producao:lista_curvas')

    if request.method == 'POST':
        form = ImportarCurvaForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    curva = CurvaCrescimento.objects.create(
                        nome=form.cleaned_data['nome'],
                        especie=form.cleaned_data['especie'],
                        rendimento_perc=form.cleaned_data['rendimento_perc']
                    )
                    df = pd.read_excel(request.FILES['arquivo_excel'])
                    
                    col_mapping = {
                        'Período': 'periodo_semana', 'Dias': 'periodo_dias',
                        'Peso Inicial': 'peso_inicial', 'Peso Final': 'peso_final',
                        'Ganho de Peso': 'ganho_de_peso', 'Nº Tratos': 'numero_tratos',
                        'Hora Início': 'hora_inicio', '% Arraç. Biomassa': 'arracoamento_biomassa_perc',
                        '% Mortalidade Presumida': 'mortalidade_presumida_perc',
                        'Ração': 'racao_nome', 'GPD': 'gpd', 'TCA': 'tca',
                    }
                    df.rename(columns=col_mapping, inplace=True)

                    racao_nao_encontrada_msgs = []
                    for index, row in df.iterrows():
                        racao_obj = None
                        racao_nome = row.get('racao_nome')
                        if racao_nome:
                            try:
                                racao_obj = Produto.objects.get(nome__iexact=racao_nome, categoria__nome__iexact='Ração')
                            except Produto.DoesNotExist:
                                racao_nao_encontrada_msgs.append(f"Linha {index + 2}: Ração '{racao_nome}' não encontrada.")
                            except Produto.MultipleObjectsReturned:
                                racao_nao_encontrada_msgs.append(f"Linha {index + 2}: Múltiplas rações '{racao_nome}'.")
                        
                        hora_inicio = None
                        hora_str = str(row.get('hora_inicio', ''))
                        if hora_str:
                            try:
                                if ':' in hora_str:
                                    parts = list(map(int, hora_str.split(':')))
                                    if len(parts) == 2: hora_inicio = time(parts[0], parts[1])
                                    elif len(parts) == 3: hora_inicio = time(parts[0], parts[1], parts[2])
                                else:
                                    total_seconds = float(hora_str) * 24 * 3600
                                    h = int(total_seconds // 3600)
                                    m = int((total_seconds % 3600) // 60)
                                    hora_inicio = time(h, m)
                            except (ValueError, TypeError):
                                pass

                        CurvaCrescimentoDetalhe.objects.create(
                            curva=curva, periodo_semana=row['periodo_semana'],
                            periodo_dias=row['periodo_dias'], peso_inicial=row['peso_inicial'],
                            peso_final=row['peso_final'], ganho_de_peso=row['ganho_de_peso'],
                            numero_tratos=row['numero_tratos'], hora_inicio=hora_inicio,
                            arracoamento_biomassa_perc=row['arracoamento_biomassa_perc'],
                            mortalidade_presumida_perc=row['mortalidade_presumida_perc'],
                            racao=racao_obj, gpd=row['gpd'], tca=row['tca'],
                        )
                
                if racao_nao_encontrada_msgs:
                    message = "Curva importada com avisos: " + "; ".join(racao_nao_encontrada_msgs)
                    app_messages.warning(message)
                else:
                    message = app_messages.success_imported(curva, source_type="Excel")

                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': message, 'redirect_url': redirect_url})
                return redirect(redirect_url)

            except Exception as e:
                error_message = f"Ocorreu um erro ao processar o arquivo: {e}"
                if "KeyError" in str(e):
                    error_message = "Verifique se todas as colunas obrigatórias estão presentes no arquivo Excel e com os nomes corretos."
                app_messages.error(error_message)
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': error_message}, status=400)
                return render(request, template, {'form': form})
        else:
            # Form is invalid
            message = "Erro de validação. Verifique os campos do formulário."
            app_messages.error(message)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': message, 'errors': form.errors}, status=400)
    else:
        form = ImportarCurvaForm()
    
    return render_ajax_or_base(request, template, {'form': form})

@login_required
@permission_required('producao.add_curvacrescimento', raise_exception=True)
def download_template_curva_view(request):
    headers = [
        'Especie', 'Curva', '%Rendimento', 'Período', 'Dias', 'Peso Inicial', 'Peso Final', 
        'Ganho de Peso', 'Nº Tratos', 'Hora Início', '% Arraç. Biomassa', 
        '% Mortalidade Presumida', 'Ração', 'GPD', 'TCA'
    ]
    df = pd.DataFrame(columns=headers)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Curva de Crescimento')
    output.seek(0)
    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="template_curva_crescimento.xlsx"'
    return response


# === Lotes ===

class ListaLotesView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Lote
    template_name = 'producao/lotes/lista_lotes.html'
    context_object_name = 'lotes'
    permission_required = 'producao.view_lote'
    raise_exception = True

    def get_queryset(self):
        from django.db.models import Sum, Case, When, DecimalField, F, OuterRef, Subquery, Value
        from django.db.models.functions import Coalesce
        
        qs = super().get_queryset()

        today = timezone.now().date()
    
        latest_ld = LoteDiario.objects.filter(
            lote=OuterRef('pk'),
            data_evento__lte=today
        ).order_by('-data_evento')

        # Anota os valores para uso no template, evitando o conflito com as propriedades do modelo
        qs = qs.annotate(
            entradas=Coalesce(
                Sum('eventos_manejo__quantidade', 
                    filter=Q(eventos_manejo__tipo_evento__nome='Povoamento') | Q(eventos_manejo__tipo_movimento='Entrada')),
                Value(0, output_field=DecimalField())
            ),
            saidas=Coalesce(
                Sum('eventos_manejo__quantidade', 
                    filter=Q(eventos_manejo__tipo_evento__nome__in=['Mortalidade', 'Despesca']) | Q(eventos_manejo__tipo_movimento='Saída')),
                Value(0, output_field=DecimalField())
            ),
            qtd_atual_annotated=F('entradas') - F('saidas'),
            peso_atual_annotated=Coalesce(
                Subquery(latest_ld.values('peso_medio_real')[:1]),
                Subquery(latest_ld.values('peso_medio_projetado')[:1]),
                F('peso_medio_inicial'),
                output_field=DecimalField()
            )
        )
        # A biomassa também precisa ser anotada, pois depende dos valores acima
        qs = qs.annotate(
            biomassa_atual_kg_annotated=(F('qtd_atual_annotated') * F('peso_atual_annotated')) / 1000
        )

        termo = self.request.GET.get('termo_lote', '').strip()
        if termo:
            qs = qs.filter(
                Q(nome__icontains=termo) |
                Q(curva_crescimento__nome__icontains=termo) |
                Q(fase_producao__nome__icontains=termo) |
                Q(tanque_atual__nome__icontains=termo)
            )
        return qs

    def render_to_response(self, context, **response_kwargs):
        context['termo_busca'] = self.request.GET.get('termo_lote', '').strip()
        return render_ajax_or_base(self.request, self.template_name, context)


class CadastrarLoteView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = Lote
    form_class = LoteForm
    template_name = 'producao/lotes/cadastrar_lote.html'
    success_url = reverse_lazy('producao:lista_lotes')
    permission_required = 'producao.add_lote'
    raise_exception = True

    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)


class EditarLoteView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = Lote
    form_class = LoteForm
    template_name = 'producao/lotes/editar_lote.html'
    success_url = reverse_lazy('producao:lista_lotes')
    permission_required = 'producao.change_lote'
    raise_exception = True

    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)


class ExcluirLotesMultiplosView(BulkDeleteView):
    model = Lote
    permission_required = 'producao.delete_lote'
    success_url_name = 'producao:lista_lotes'

    def post(self, request, *args, **kwargs):
        app_messages = get_app_messages(request)
        try:
            data = json.loads(request.body)
            ids = data.get('ids', [])
            if not ids:
                message = app_messages.error('Nenhum item selecionado para exclusão.')
                return JsonResponse({'success': False, 'message': message}, status=400)

            lotes_para_deletar = self.model.objects.filter(pk__in=ids)
            deleted_names = [str(obj) for obj in lotes_para_deletar]

            with transaction.atomic():
                # CORRECAO: Deletar filhos explicitamente primeiro
                LoteDiario.objects.filter(lote__in=lotes_para_deletar).delete()
                
                # Agora, deletar os lotes 'pais'
                deleted_count, _ = lotes_para_deletar.delete()

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
            error_message = f'Ocorreu um erro inesperado: {e}'
            message = app_messages.error(error_message)
            return JsonResponse({'success': False, 'message': message}, status=500)

# === Eventos de Manejo ===

class ListaEventosView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = EventoManejo
    template_name = 'producao/eventos/lista_eventos.html'
    context_object_name = 'eventos'
    permission_required = 'producao.view_eventomanejo'
    raise_exception = True

    def get_queryset(self):
        qs = super().get_queryset().select_related('lote', 'tanque_origem', 'tanque_destino')

        # Filtros
        tipo_evento = self.request.GET.get('tipo_evento', '').strip()
        tanque_origem_id = self.request.GET.get('tanque_origem', '').strip()
        tanque_destino_id = self.request.GET.get('tanque_destino', '').strip()
        lote_id = self.request.GET.get('lote', '').strip()
        data_evento = self.request.GET.get('data_evento', '').strip()

        if tipo_evento:
            qs = qs.filter(tipo_evento_id=tipo_evento)
        if tanque_origem_id:
            qs = qs.filter(tanque_origem_id=tanque_origem_id)
        if tanque_destino_id:
            qs = qs.filter(tanque_destino_id=tanque_destino_id)
        if lote_id:
            qs = qs.filter(lote_id=lote_id)
        if data_evento:
            try:
                data_formatada = datetime.strptime(data_evento, '%Y-%m-%d').date()
                qs = qs.filter(data_evento=data_formatada)
            except (ValueError, TypeError):
                pass

        return qs.order_by('-data_evento', '-id')

    def render_to_response(self, context, **response_kwargs):
        context['tipos_evento'] = TipoEvento.objects.all()
        context['tanques'] = Tanque.objects.all().order_by('nome')
        context['lotes'] = Lote.objects.all().order_by('nome')
        context['filtros'] = {
            'tipo_evento': self.request.GET.get('tipo_evento', ''),
            'tanque_origem': self.request.GET.get('tanque_origem', ''),
            'tanque_destino': self.request.GET.get('tanque_destino', ''),
            'lote': self.request.GET.get('lote', ''),
            'data_evento': self.request.GET.get('data_evento', ''),
        }
        return render_ajax_or_base(self.request, self.template_name, context)


from django.contrib import messages
from decimal import Decimal

class RegistrarEventoView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = EventoManejo
    form_class = EventoManejoForm
    template_name = 'producao/eventos/registrar_evento.html'
    success_url = reverse_lazy('producao:lista_eventos')
    permission_required = 'producao.add_eventomanejo'
    raise_exception = True

    def form_valid(self, form):
        try:
            with transaction.atomic():
                evento = form.save(commit=False)

                if evento.tipo_evento == 'Transferencia':
                    # --- LOGICA DE ORQUESTRACAO DE TRANSFERENCIA ---
                    lote_origem = evento.lote
                    tanque_destino = evento.tanque_destino
                    quantidade_transferida = evento.quantidade
                    peso_medio_transferido = evento.peso_medio
                    is_transferencia_total = evento.transferencia_total

                    if not all([lote_origem, tanque_destino, quantidade_transferida, peso_medio_transferido]):
                        form.add_error(None, "Para transferências, o lote de origem, tanque de destino, quantidade e peso são obrigatórios.")
                        return self.form_invalid(form)
                    
                    tanque_origem_obj = obter_tanque_lote_em_data(lote_origem, evento.data_evento)

                    # Cenário 1: Tanque de destino já tem um lote ativo
                    lote_destino_existente = Lote.objects.filter(tanque_atual=tanque_destino, ativo=True).first()

                    if lote_destino_existente:
                        # Cria um evento de ENTRADA no lote de destino
                        EventoManejo.objects.create(
                            tipo_evento='Transferencia',
                            tipo_movimento='Entrada',
                            lote=lote_destino_existente,
                            tanque_origem=tanque_origem_obj,
                            tanque_destino=tanque_destino,
                            data_evento=evento.data_evento,
                            quantidade=quantidade_transferida,
                            peso_medio=peso_medio_transferido,
                            observacoes=f"Entrada por transferência do lote {lote_origem.nome}."
                        )
                    else:
                        # Cenário 2: Tanque de destino está vazio
                        novo_lote = Lote.objects.create(
                            nome=lote_origem.nome,
                            curva_crescimento=lote_origem.curva_crescimento,
                            fase_producao=lote_origem.fase_producao,
                            tanque_atual=tanque_destino,
                            quantidade_inicial=quantidade_transferida,
                            peso_medio_inicial=peso_medio_transferido,
                            data_povoamento=evento.data_evento,
                            ativo=True
                        )
                        EventoManejo.objects.create(
                            tipo_evento='Povoamento',
                            tipo_movimento='Entrada',
                            lote=novo_lote,
                            tanque_origem=tanque_origem_obj,
                            tanque_destino=tanque_destino,
                            data_evento=evento.data_evento,
                            quantidade=quantidade_transferida,
                            peso_medio=peso_medio_transferido,
                            observacoes=f"Lote criado a partir da transferência do lote {lote_origem.nome}."
                        )

                    # Cria o evento de SAÍDA no lote de origem
                    evento.tipo_movimento = 'Saída'
                    evento.save()

                    # Se for transferência total, desativa o lote de origem e libera o tanque
                    if is_transferencia_total:
                        lote_origem.ativo = False
                        lote_origem.tanque_atual = None
                        lote_origem.save(update_fields=['ativo', 'tanque_atual'])
                        
                        if tanque_origem_obj:
                            tanque_origem_obj.verificar_e_liberar_status()

                    # A lógica de recalcular_estado_atual será chamada pelos sinais de post_save do EventoManejo

                    app_messages = get_app_messages(self.request)
                    message = f"Transferência de {quantidade_transferida} peixes do lote {lote_origem.nome} processada com sucesso."
                    
                    if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({'success': True, 'message': message, 'redirect_url': str(self.get_success_url())})
                    
                    messages.success(self.request, message)
                    return redirect(self.get_success_url())

                else:
                    # Comportamento padrão para todos os outros tipos de evento
                    return super().form_valid(form)

        except Exception as e:
            # Adiciona logging do erro para depuração
            logging.exception("Erro ao processar evento de manejo.")
            form.add_error(None, f"Ocorreu um erro inesperado ao processar o evento: {e}")
            return self.form_invalid(form)

    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)


class EditarEventoView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = EventoManejo
    form_class = EventoManejoForm
    template_name = 'producao/eventos/editar_evento.html'
    success_url = reverse_lazy('producao:lista_eventos')
    permission_required = 'producao.change_eventomanejo'
    raise_exception = True

    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)


class ExcluirEventosMultiplosView(BulkDeleteView):
    model = EventoManejo
    permission_required = 'producao.delete_eventomanejo'
    success_url_name = 'producao:lista_eventos'


from django.forms.models import model_to_dict
from decimal import Decimal, InvalidOperation

def _to_decimal(s):
    if s is None:
        return None
    val = str(s).strip()
    if not val:
        return None
    
    # Detecta se o formato é brasileiro (ex: "1.234,56")
    # A heurística é a presença de vírgula como último separador.
    last_comma = val.rfind(',')
    last_dot = val.rfind('.')
    
    if last_comma > last_dot:
        # Formato brasileiro: "1.234,56" -> "1234.56"
        val = val.replace('.', '').replace(',', '.')
    # Se for formato americano ("1,234.56"), removemos apenas a vírgula
    elif last_dot > last_comma:
        val = val.replace(',', '')
        
    try:
        return Decimal(val)
    except InvalidOperation:
        return None

@login_required
@require_http_methods(["GET"])
def tanque_detail(request, pk):
    obj = get_object_or_404(Tanque, pk=pk)
    d = model_to_dict(obj)
    # normaliza formatos para o front
    d["data_criacao"] = obj.data_criacao.strftime("%Y-%m-%d %H:%M:%S") if obj.data_criacao else ""
    # garante numéricos como float
    for f in ("largura","comprimento","profundidade","metro_quadrado","metro_cubico","ha"):
        if f in d and d[f] is not None:
            d[f] = float(d[f])
    # Adiciona o ID do tipo_tela ao dicionário para o frontend
    d["tipo_tela"] = obj.tipo_tela_id if obj.tipo_tela else None

    return JsonResponse(d, safe=False)

@login_required
@require_http_methods(["POST"])
def tanque_update(request, pk):
    obj = get_object_or_404(Tanque, pk=pk)

    obj.nome = request.POST.get("nome","")
    obj.sequencia = request.POST.get("sequencia") or None
    obj.tag_tanque = request.POST.get("tag_tanque") or ""

    obj.largura = _to_decimal(request.POST.get("largura"))
    obj.comprimento = _to_decimal(request.POST.get("comprimento"))
    obj.profundidade = _to_decimal(request.POST.get("profundidade"))

    # calculados (se vierem, usa; senão recalcula)
    mq = _to_decimal(request.POST.get("metro_quadrado"))
    mc = _to_decimal(request.POST.get("metro_cubico"))
    ha = _to_decimal(request.POST.get("ha"))
    if mq is None and obj.largura and obj.comprimento:
        mq = obj.largura * obj.comprimento
    if mc is None and mq is not None and obj.profundidade:
        mc = mq * obj.profundidade
    if ha is None and mq is not None:
        ha = mq / Decimal("10000")
    obj.metro_quadrado = mq
    obj.metro_cubico = mc
    obj.ha = ha

    # FKs por *_id
    for campo in ("unidade","fase","tipo_tanque","linha_producao","malha","status_tanque","tipo_tela"):
        v = request.POST.get(f"{campo}")
        if v: setattr(obj, f"{campo}_id", int(v))

    ativo = request.POST.get("ativo")
    if ativo is not None:
        obj.ativo = ativo in ("1","true","True","on","True")

    obj.save()
    return JsonResponse({"success": True, "message": "Tanque atualizado com sucesso.", "id": obj.id})

@login_required
@require_http_methods(["POST"])
def tanque_create(request):
    # reusa a lógica do update mudando a criação
    novo = Tanque()
    # preenche igual ao update (pode extrair para função comum se preferir)...
    novo.nome = request.POST.get("nome","")
    novo.sequencia = request.POST.get("sequencia") or None
    novo.tag_tanque = request.POST.get("tag_tanque") or ""

    novo.largura = _to_decimal(request.POST.get("largura"))
    novo.comprimento = _to_decimal(request.POST.get("comprimento"))
    novo.profundidade = _to_decimal(request.POST.get("profundidade"))

    # calculados (se vierem, usa; senão recalcula)
    mq = _to_decimal(request.POST.get("metro_quadrado"))
    mc = _to_decimal(request.POST.get('metro_cubico'))
    ha = _to_decimal(request.POST.get("ha"))
    if mq is None and novo.largura and novo.comprimento:
        mq = novo.largura * novo.comprimento
    if mc is None and mq is not None and novo.profundidade:
        mc = mq * novo.profundidade
    if ha is None and mq is not None:
        ha = mq / Decimal("10000")
    novo.metro_quadrado = mq
    novo.metro_cubico = mc
    novo.ha = ha

    # FKs por *_id
    for campo in ("unidade","fase","tipo_tanque","linha_producao","malha","status_tanque","tipo_tela"):
        v = request.POST.get(f"{campo}")
        if v: setattr(novo, f"{campo}_id", int(v))

    ativo = request.POST.get("ativo")
    if ativo is not None:
        novo.ativo = ativo in ("1","true","True","on","True")

    novo.save()
    return JsonResponse({"success": True, "message": "Tanque criado com sucesso.", "id": novo.id})

@login_required
@permission_required('producao.view_tanque', raise_exception=True)
def gerenciar_tanques_view(request):
    """
    Renderiza a página principal de gerenciamento de tanques.
    """
    context = {
        'tanques': Tanque.objects.all().order_by('nome'),
        'form_tanque': TanqueForm(),
        'data_page': 'gerenciar-tanques',
        'data_tela': 'gerenciar-tanques',
    }
    return render_ajax_or_base(request, 'producao/gerenciar_tanques.html', context)


@login_required
@permission_required('producao.view_curvacrescimento')
def gerenciar_curvas(request):
    """
    Renderiza a página principal de gerenciamento de curvas,
    já com os formulários e a lista inicial de curvas.
    """
    context = {
        'curvas': CurvaCrescimento.objects.all().order_by('nome'),
        'form_curva': CurvaCrescimentoForm(),
        'form_detalhe': CurvaCrescimentoDetalheForm(),
        'data_page': 'gerenciar-curvas', # Para o JS saber qual tela ativar
        'data_tela': 'gerenciar-curvas',
    }
    return render_ajax_or_base(request, 'producao/curvas/gerenciar_curvas.html', context)


# =========================================================================
# API Views para Gerenciamento de Curvas (JSON)
# =========================================================================

# -----------------------------
# Helpers de serialização
# -----------------------------

def _to_float(x):
    if x is None or x == "":
        return None
    try:
        return float(x)
    except (ValueError, TypeError):
        return x

def serialize_curva(curva: CurvaCrescimento) -> dict:
    return {
        "id": curva.pk,
        "nome": curva.nome,
        "especie": curva.especie,
        "rendimento_perc": _to_float(curva.rendimento_perc),
        "trato_perc_curva": _to_float(curva.trato_perc_curva),
        "peso_pretendido": _to_float(curva.peso_pretendido),
        "trato_sabados_perc": _to_float(curva.trato_sabados_perc),
        "trato_domingos_perc": _to_float(curva.trato_domingos_perc),
        "trato_feriados_perc": _to_float(curva.trato_feriados_perc),
    }

def serialize_detalhe(d: CurvaCrescimentoDetalhe) -> dict:
    racao_nome = getattr(d.racao, "nome", str(d.racao)) if hasattr(d, "racao") and d.racao else None
    
    return {
        "id": d.pk,
        "periodo_semana": _to_float(d.periodo_semana),
        "periodo_dias": _to_float(d.periodo_dias),
        "peso_inicial": _to_float(d.peso_inicial),
        "peso_final": _to_float(d.peso_final),
        "ganho_de_peso": _to_float(d.ganho_de_peso),
        "numero_tratos": _to_float(d.numero_tratos),
        "hora_inicio": d.hora_inicio.strftime("%H:%M") if d.hora_inicio else None,
        "arracoamento_biomassa_perc": _to_float(d.arracoamento_biomassa_perc),
        "mortalidade_presumida_perc": _to_float(d.mortalidade_presumida_perc),
        "racao": d.racao_id,
        "racao_nome": racao_nome,
        "gpd": _to_float(d.gpd),
        "tca": _to_float(d.tca),
    }

# -----------------------------
# Endpoints
# -----------------------------

@login_required
@require_http_methods(["GET"])
@permission_required('producao.view_curvacrescimento', raise_exception=True)
def curva_com_detalhes_view(request, curva_id: int):
    """
    GET /producao/api/curva/<id>/detalhes/
    """
    curva = get_object_or_404(CurvaCrescimento, pk=curva_id)
    detalhes_qs = CurvaCrescimentoDetalhe.objects.filter(curva=curva).order_by("periodo_semana", "pk")
    payload = {
        "curva": serialize_curva(curva),
        "detalhes": [serialize_detalhe(d) for d in detalhes_qs]
    }
    return JsonResponse(payload, status=200)

@login_required
@require_http_methods(["GET"])
@permission_required('producao.view_curvacrescimento', raise_exception=True)
def detalhe_view(request, curva_id: int, detalhe_id: int):
    """
    GET /producao/api/curva/<id>/detalhes/<detalhe_id>/
    """
    curva = get_object_or_404(CurvaCrescimento, pk=curva_id)
    detalhe = get_object_or_404(CurvaCrescimentoDetalhe, pk=detalhe_id, curva=curva)
    return JsonResponse(serialize_detalhe(detalhe), status=200)

@login_required
@require_http_methods(["POST"])
@permission_required('producao.add_curvacrescimento', raise_exception=True)
@transaction.atomic
def curva_create_view(request):
    """
    POST /producao/api/curva/
    """
    form = CurvaCrescimentoForm(request.POST)
    if form.is_valid():
        curva = form.save()
        app_messages = get_app_messages(request)
        message = app_messages.success_created(curva)
        return JsonResponse({"success": True, "id": curva.pk, "message": message, "curva_nome": curva.nome, "curva_especie": curva.especie}, status=201)
    app_messages = get_app_messages(request)
    message = app_messages.error("Erro ao criar curva.")
    return JsonResponse({"success": False, "errors": form.errors, "message": message}, status=400)

@login_required
@require_http_methods(["POST"])
@permission_required('producao.change_curvacrescimento', raise_exception=True)
@transaction.atomic
def curva_update_view(request, curva_id: int):
    """
    POST /producao/api/curva/<id>/
    """
    curva = get_object_or_404(CurvaCrescimento, pk=curva_id)
    form = CurvaCrescimentoForm(request.POST, instance=curva)
    if form.is_valid():
        curva = form.save()
        app_messages = get_app_messages(request)
        message = app_messages.success_updated(curva)
        return JsonResponse({"success": True, "message": message, "curva_nome": curva.nome, "curva_especie": curva.especie}, status=200)
    app_messages = get_app_messages(request)
    message = app_messages.error("Erro ao atualizar curva.")
    return JsonResponse({"success": False, "errors": form.errors, "message": message}, status=400)

@login_required
@require_http_methods(["POST"])
@permission_required('producao.add_curvacrescimentodetalhe', raise_exception=True)
@transaction.atomic
def detalhe_create_view(request, curva_id: int):
    """
    POST /producao/api/curva/<id>/detalhes/
    """
    curva = get_object_or_404(CurvaCrescimento, pk=curva_id)
    form = CurvaCrescimentoDetalheForm(request.POST)
    if form.is_valid():
        detalhe = form.save(commit=False)
        detalhe.curva = curva
        detalhe.save()
        return JsonResponse({
            "success": True,
            "message": "Período adicionado.",
            "periodo": serialize_detalhe(detalhe)
        }, status=201)
    return JsonResponse({"success": False, "errors": form.errors, "message": "Erro ao adicionar período."}, status=400)

@login_required
@require_http_methods(["POST"])
@permission_required('producao.change_curvacrescimentodetalhe', raise_exception=True)
@transaction.atomic
def detalhe_update_view(request, curva_id: int, detalhe_id: int):
    logging.info(f"--- Iniciando detalhe_update_view para detalhe_id: {detalhe_id} ---")
    logging.info(f"Dados do POST recebidos: {request.POST}")
    try:
        curva = get_object_or_404(CurvaCrescimento, pk=curva_id)
        detalhe = get_object_or_404(CurvaCrescimentoDetalhe, pk=detalhe_id, curva=curva)
        form = CurvaCrescimentoDetalheForm(request.POST, instance=detalhe)
        
        if form.is_valid():
            logging.info("Formulário é válido. Salvando...")
            detalhe = form.save()
            logging.info(f"Formulário salvo com sucesso. ID da ração no objeto salvo: {detalhe.racao_id}")
            
            logging.info("Iniciando serialização...")
            periodo_serializado = serialize_detalhe(detalhe)
            logging.info(f"Serialização concluída com sucesso: {periodo_serializado}")
            
            return JsonResponse({
                "success": True,
                "message": "Período atualizado.",
                "periodo": periodo_serializado
            }, status=200)
        else:
            logging.error(f"Formulário inválido. Erros: {form.errors.as_json()}")
            return JsonResponse({"success": False, "errors": form.errors, "message": "Erro ao atualizar período."}, status=400)
            
    except Exception as e:
        logging.exception("Ocorreu uma exceção não tratada na view detalhe_update_view")
        return JsonResponse({"success": False, "message": f"Erro inesperado no servidor: {str(e)}"}, status=500)


# === Povoamento de Lotes ===

@login_required
@permission_required('producao.add_lote', raise_exception=True)
def povoamento_lotes_view(request):
    app_messages = get_app_messages(request)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            povoamentos = data.get('povoamentos', [])
            if not povoamentos:
                return JsonResponse({'success': False, 'message': app_messages.custom_error('Nenhum dado de povoamento recebido.')}, status=400)

            with transaction.atomic():
                for item in povoamentos:
                    form = PovoamentoForm(item)
                    if not form.is_valid():
                        # Retorna o primeiro erro de validação encontrado
                        primeiro_erro_campo = next(iter(form.errors))
                        primeiro_erro_msg = form.errors[primeiro_erro_campo][0]
                        return JsonResponse({'success': False, 'message': f'Erro na validação: {primeiro_erro_campo} - {primeiro_erro_msg}'}, status=400)

                    cleaned_data = form.cleaned_data
                    tanque = get_object_or_404(Tanque, pk=cleaned_data['tanque_id'])

                    # Lógica de decisão baseada na existência de um lote ativo no tanque
                    lote_ativo_existe = Lote.objects.filter(tanque_atual=tanque, ativo=True).exists()

                    if lote_ativo_existe:
                        # TANQUE JÁ POVOADO: Adiciona a um lote existente (Reforço)
                        try:
                            lote_existente = Lote.objects.get(tanque_atual=tanque, ativo=True)
                            
                            # Cria o evento de classificação para adicionar ao lote
                            EventoManejo.objects.create(
                                tipo_evento='Povoamento', 
                                lote=lote_existente,
                                tanque_destino=tanque,
                                data_evento=cleaned_data['data_lancamento'],
                                quantidade=cleaned_data['quantidade'],
                                peso_medio=cleaned_data['peso_medio'],
                                observacoes=f"Reforço ao lote existente. Origem: {cleaned_data.get('grupo_origem', 'N/A')}",
                                tipo_movimento='Entrada' # Adicionado para povoamento/reforço
                            )

                            # Recalcula o estado do lote após o reforço
                            # lote_existente.recalcular_estado_atual()

                        except Lote.MultipleObjectsReturned:
                            return JsonResponse({'success': False, 'message': f"Erro de Dados: Múltiplos lotes ativos encontrados no tanque '{tanque.nome}'. Corrija o cadastro."}, status=400)
                        # O caso DoesNotExist é coberto pelo .exists() acima, então não deve ocorrer.

                    else:
                        # TANQUE LIVRE: Cria um novo lote
                        novo_lote = Lote.objects.create(
                            nome=cleaned_data['nome_lote'],
                            curva_crescimento_id=cleaned_data.get('curva_id'),
                            fase_producao_id=cleaned_data.get('fase_id'),
                            tanque_atual=tanque,
                            quantidade_inicial=cleaned_data['quantidade'],
                            peso_medio_inicial=cleaned_data['peso_medio'],
                            data_povoamento=cleaned_data['data_lancamento'],
                            ativo=True
                        )
                        EventoManejo.objects.create(
                            tipo_evento='Povoamento',
                            lote=novo_lote,
                            tanque_destino=tanque,
                            data_evento=cleaned_data['data_lancamento'],
                            quantidade=cleaned_data['quantidade'],
                            peso_medio=cleaned_data['peso_medio'],
                            tipo_movimento='Entrada' # Adicionado para povoamento inicial
                        )
                        
                        # Recalcula o estado do lote, que também vai cuidar de atualizar o status do tanque
                        # novo_lote.recalcular_estado_atual()

                        # --- INICIO DA NOVA INTEGRACAO ---
                        from .utils import projetar_ciclo_de_vida_lote
                        
                        try:
                            projetar_ciclo_de_vida_lote(novo_lote)
                        except Exception as e:
                            # Logar o erro de projeção, mas não impedir o sucesso do povoamento.
                            # É crucial que o povoamento não falhe se a projeção tiver um problema.
                            logging.error(f"Erro ao projetar o ciclo de vida para o novo lote {novo_lote.id}: {e}")
                        # --- FIM DA NOVA INTEGRACAO ---
            
            success_message = app_messages.success_process(f'{len(povoamentos)} povoamento(s) processado(s) com sucesso!')
            return JsonResponse({'success': True, 'message': success_message})

        except Exception as e:
            error_message = app_messages.error(f'Ocorreu um erro inesperado: {e}')
            return JsonResponse({'success': False, 'message': error_message}, status=500)

    # Prepara dados enriquecidos para o frontend
    tanques = Tanque.objects.select_related('status_tanque', 'fase').order_by('nome')
    lotes_ativos_qs = Lote.objects.filter(ativo=True, tanque_atual__isnull=False)
    lotes_ativos_tanque_ids = set(lotes_ativos_qs.values_list('tanque_atual_id', flat=True))

    tanques_data = []
    for tanque in tanques:
        tem_lote_ativo = tanque.pk in lotes_ativos_tanque_ids
        ocupacao_percentual = 100 if tem_lote_ativo else 0
        tanques_data.append({
            'pk': tanque.pk,
            'nome': tanque.nome,
            'status_nome': tanque.status_tanque.nome.lower() if tanque.status_tanque else '',
            'tem_lote_ativo': tem_lote_ativo,
            'ocupacao_percentual': ocupacao_percentual,
            'fase_nome': tanque.fase.nome if tanque.fase else '',
            'fase_id': tanque.fase_id,
        })

    fases_list = list(FaseProducao.objects.values('pk', 'nome'))
    linhas_list = list(LinhaProducao.objects.values('pk', 'nome'))

    context = {
        'curvas': CurvaCrescimento.objects.order_by('nome'),
        'tanques_data': tanques_data,
        'fases_list': fases_list,
        'linhas_list': linhas_list,
        'tipos_evento': TipoEvento.objects.all(),
        'data_page': 'povoamento-lotes'
    }
    return render_ajax_or_base(request, 'producao/povoamento_lotes.html', context)

@login_required
def historico_povoamento_view(request):
    """Filtra e retorna o histórico de eventos de manejo."""
    try:
        data_inicial = request.GET.get('data_inicial')
        data_final = request.GET.get('data_final')
        status = request.GET.get('status')  # Pode ser ID do tipo_evento

        # Base queryset
        eventos = EventoManejo.objects.select_related(
            'lote', 'tanque_origem', 'tanque_destino', 'tipo_evento'
        ).order_by('-data_evento', '-id')

        # Aplicar filtros de data
        if data_inicial:
            eventos = eventos.filter(data_evento__gte=data_inicial)
        if data_final:
            eventos = eventos.filter(data_evento__lte=data_final)

        # Filtro por status (ID do tipo_evento)
        if status and status.isdigit():
            eventos = eventos.filter(tipo_evento_id=status)

        # Limitar resultados
        eventos = eventos[:100]        # Construir lista de dicionários
        data = []
        resolvedores_tanque = {}
        for evento in eventos:
            tanque_fallback = None
            if evento.lote:
                if evento.lote_id not in resolvedores_tanque:
                    resolvedores_tanque[evento.lote_id] = construir_resolvedor_tanque_lote(evento.lote)
                tanque_fallback = resolvedores_tanque[evento.lote_id](evento.data_evento)
            data.append({
                'id': evento.id,
                'data': evento.data_evento.strftime('%d/%m/%Y'),
                'lote_nome': evento.lote.nome if evento.lote else 'N/A',
                'tanque_nome': (evento.tanque_destino.nome if evento.tanque_destino else (evento.tanque_origem.nome if evento.tanque_origem else (tanque_fallback.nome if tanque_fallback else 'N/A'))),
                'tanque_origem_nome': evento.tanque_origem.nome if evento.tanque_origem else 'N/A',
                'tanque_destino_nome': evento.tanque_destino.nome if evento.tanque_destino else 'N/A',
                'quantidade': evento.quantidade,
                'peso_medio': evento.peso_medio,
                'status': evento.tipo_evento.nome if evento.tipo_evento else 'Desconhecido',
            })

        return JsonResponse(data, safe=False)  # Retorna array

    except Exception as e:
        # Log do erro para debug
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Erro em historico_povoamento_view")
        return JsonResponse({'error': str(e)}, status=500)
    
@login_required
@require_http_methods(["GET"])
def get_active_lote_for_tanque_api(request, tanque_id):
    """
    API endpoint para buscar o lote de um tanque.
    - Sem data_evento: retorna o lote ativo atual (comportamento legado).
    - Com data_evento=YYYY-MM-DD: retorna o lote do tanque naquela data.
    """
    try:
        data_evento_str = request.GET.get('data_evento')
        if data_evento_str:
            try:
                data_evento = datetime.strptime(data_evento_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse(
                    {'success': False, 'message': 'Formato de data inválido. Use YYYY-MM-DD.'},
                    status=400
                )

            lote_ids = list(
                LoteDiario.objects.filter(
                    tanque_id=tanque_id,
                    data_evento=data_evento
                ).values_list('lote_id', flat=True).distinct()
            )

            if not lote_ids:
                return JsonResponse(
                    {'success': False, 'message': 'Nenhum lote encontrado para o tanque na data informada.'},
                    status=404
                )

            if len(lote_ids) > 1:
                return JsonResponse(
                    {'success': False, 'message': 'Múltiplos lotes encontrados para o tanque na data informada.'},
                    status=409
                )

            lote = Lote.objects.get(id=lote_ids[0])
            return JsonResponse({'success': True, 'lote': {'id': lote.id, 'nome': lote.nome}})

        lote = Lote.objects.get(tanque_atual_id=tanque_id, ativo=True)
        return JsonResponse({'success': True, 'lote': {'id': lote.id, 'nome': lote.nome}})
    except Lote.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Nenhum lote ativo encontrado.'}, status=404)
    except Lote.MultipleObjectsReturned:
        return JsonResponse({'success': False, 'message': 'Múltiplos lotes ativos encontrados.'}, status=409)


@login_required
@permission_required('producao.add_eventomanejo', raise_exception=True)
def gerenciar_eventos_view(request):
    """
    Renderiza a página principal de gerenciamento de eventos de produção.
    """
    ultimos_eventos = EventoManejo.objects.select_related(
        'lote', 'tanque_origem', 'tanque_destino'
    ).order_by('-data_evento', '-id')[:20]

    context = {
        'unidades': Unidade.objects.all().order_by('nome'),
        'linhas_producao': LinhaProducao.objects.all().order_by('nome'),
        'fases_producao': FaseProducao.objects.all().order_by('nome'),
        'tipos_evento': TipoEvento.objects.all().order_by('nome'),
        'ultimos_eventos': ultimos_eventos,
        'data_page': 'gerenciar-eventos',
        'data_tela': 'gerenciar-eventos',
    }
    return render_ajax_or_base(request, 'producao/eventos/gerenciar_eventos.html', context)

@login_required
@require_http_methods(["GET"])
@permission_required('producao.view_lote', raise_exception=True)
def get_lotes_ativos_api(request):
    lotes = Lote.objects.filter(ativo=True).select_related('tanque_atual', 'fase_producao').order_by('nome')
    data = []
    for lote in lotes:
        data.append({
            'id': lote.id,
            'nome': lote.nome,
            'tanque': lote.tanque_atual.nome if lote.tanque_atual else 'N/A',
            'fase': lote.fase_producao.nome if lote.fase_producao else 'N/A',
        })
    return JsonResponse(data, safe=False)

@login_required
@require_http_methods(["GET"])
@permission_required('producao.view_lote', raise_exception=True)
def api_mortalidade_lotes_ativos(request):
    # Lógica de anotação para calcular a quantidade atual no banco de dados
    base_query = Lote.objects.filter(ativo=True)

    # Anota as entradas e saídas totais para cada lote
    annotated_lotes = base_query.annotate(
        total_entradas=Sum(
            Case(
                When(Q(eventos_manejo__tipo_evento__nome='Povoamento') | Q(eventos_manejo__tipo_movimento='Entrada'), then='eventos_manejo__quantidade'),
                default=Value(0),
                output_field=DecimalField()
            )
        ),
        total_saidas=Sum(
            Case(
                When(Q(eventos_manejo__tipo_evento__nome__in=['Mortalidade', 'Despesca']) | Q(eventos_manejo__tipo_movimento='Saída'), then='eventos_manejo__quantidade'),
                default=Value(0),
                output_field=DecimalField()
            )
        )
    )

    # Calcula a quantidade atual e filtra os lotes elegíveis
    lotes_qs = annotated_lotes.annotate(
        quantidade_atual_calculada=F('total_entradas') - F('total_saidas')
    ).filter(
        quantidade_atual_calculada__gt=0
    ).select_related(
        'tanque_atual', 'fase_producao'
    ).order_by('tanque_atual__sequencia', 'nome')

    # Lógica de filtro que o frontend já envia
    unidade_id = request.GET.get('unidade')
    linha_id = request.GET.get('linha_producao')
    fase_id = request.GET.get('fase')
    termo = request.GET.get('termo', '').strip()

    if unidade_id:
        lotes_qs = lotes_qs.filter(tanque_atual__unidade_id=unidade_id)
    if linha_id:
        lotes_qs = lotes_qs.filter(tanque_atual__linha_producao_id=linha_id)
    if fase_id:
        lotes_qs = lotes_qs.filter(fase_producao_id=fase_id)
    if termo:
        lotes_qs = lotes_qs.filter(Q(nome__icontains=termo) | Q(tanque_atual__nome__icontains=termo))

    results = []
    for lote in lotes_qs:
        biomassa_kg = (lote.quantidade_atual * lote.peso_medio_atual) / 1000 if lote.quantidade_atual and lote.peso_medio_atual else 0
        results.append({
            'lote_id': lote.id,
            'tanque': lote.tanque_atual.nome if lote.tanque_atual else 'N/A',
            'lote': lote.nome,
            'data_inicio': lote.data_povoamento.strftime('%d/%m/%Y'),
            'qtd_atual': f'{lote.quantidade_atual:.0f}',
            'peso_medio_g': f'{lote.peso_medio_atual:.2f}' if lote.peso_medio_atual else '0.00',
            'biomassa_kg': f'{biomassa_kg:.2f}',
            'qtd_mortalidade': '', # Campo para o input do usuário
            'tanque_id': lote.tanque_atual_id,
            'tipo_movimento': 'Saída',
        })

    return JsonResponse({'results': results})

@login_required
@require_http_methods(["POST"])
@permission_required('producao.add_eventomanejo', raise_exception=True)
@transaction.atomic
def processar_mortalidade_api(request):
    try:
        data = json.loads(request.body)
        registros = data.get('lancamentos', [])
        data_evento_str = data.get('data_evento')
        if not data_evento_str:
            return JsonResponse({'success': False, 'message': 'A data do evento é obrigatória.'}, status=400)
        try:
            data_evento = datetime.strptime(data_evento_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Formato de data inválido. Use YYYY-MM-DD.'}, status=400)

        for registro in registros:
            lote_id = registro.get('lote_id')
            mortalidade = Decimal(registro.get('quantidade_mortalidade', 0))

            if mortalidade > 0:
                try:
                    lote = get_object_or_404(Lote, id=lote_id, ativo=True)
                    
                    evento = EventoManejo.objects.create(
                        tipo_evento='Mortalidade',
                        lote=lote,
                        tanque_origem_id=registro.get('tanque_origem_id'),
                        tipo_movimento=registro.get('tipo_movimento'),
                        data_evento=data_evento,
                        quantidade=mortalidade,
                        peso_medio=lote.peso_medio_atual,
                        observacoes=f"Registro de mortalidade em massa."
                    )
                    
                    lote.recalcular_estado_atual()
                except Lote.DoesNotExist:
                    continue
                except Exception as inner_e:
                    continue
        
        return JsonResponse({'success': True, 'message': 'Registros de mortalidade processados com sucesso.'})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Requisição JSON inválida.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro interno do servidor: {e}'}, status=500)

@login_required
@require_http_methods(["POST"])
@permission_required('producao.add_eventomanejo', raise_exception=True)
def registrar_mortalidade_api(request):
    try:
        data = json.loads(request.body)
        lote_id = data.get('lote_id')
        quantidade = Decimal(data.get('quantidade'))
        data_evento = data.get('data_evento')

        lote = get_object_or_404(Lote, id=lote_id, ativo=True)

        EventoManejo.objects.create(
            tipo_evento='Mortalidade',
            lote=lote,
            data_evento=data_evento,
            quantidade=quantidade,
            peso_medio=lote.peso_medio_atual,
            observacoes='Registro de mortalidade individual.'
        )
        lote.recalcular_estado_atual()
        return JsonResponse({'success': True, 'message': 'Mortalidade registrada com sucesso.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@login_required
@require_http_methods(["GET"])
def api_ultimos_eventos(request):
    offset = int(request.GET.get('offset', 0))
    limit = 20

    # Correção definitiva: prefetch_related para garantir LEFT OUTER JOIN no lote
    eventos_qs = EventoManejo.objects.select_related(
        'lote', 'tanque_origem', 'tanque_destino'
    ).order_by('-data_evento', '-id')

    # Filtros da interface
    termo = request.GET.get('termo', '').strip()
    unidade_id = request.GET.get('unidade')
    linha_id = request.GET.get('linha_producao')
    fase_id = request.GET.get('fase')
    data_str = request.GET.get('data')

    if termo:
        eventos_qs = eventos_qs.filter(
            Q(lote__nome__icontains=termo) |
            Q(tanque_origem__nome__icontains=termo) |
            Q(tanque_destino__nome__icontains=termo) |
            Q(observacoes__icontains=termo)
        )
    if unidade_id:
        eventos_qs = eventos_qs.filter(
            Q(tanque_origem__unidade_id=unidade_id) |
            Q(tanque_destino__unidade_id=unidade_id) |
            (
                Q(tanque_origem__isnull=True, tanque_destino__isnull=True) &
                Q(lote__tanque_atual__unidade_id=unidade_id)
            )
        )
    if linha_id:
        eventos_qs = eventos_qs.filter(
            Q(tanque_origem__linha_producao_id=linha_id) |
            Q(tanque_destino__linha_producao_id=linha_id) |
            (
                Q(tanque_origem__isnull=True, tanque_destino__isnull=True) &
                Q(lote__tanque_atual__linha_producao_id=linha_id)
            )
        )
    if fase_id:
        eventos_qs = eventos_qs.filter(lote__fase_producao_id=fase_id)
    if data_str:
        try:
            from datetime import datetime
            data_filtro = datetime.strptime(data_str, '%Y-%m-%d').date()
            eventos_qs = eventos_qs.filter(data_evento=data_filtro)
        except (ValueError, TypeError):
            pass # Ignora data inválida

    eventos = eventos_qs[offset:offset + limit]

    data = [{
        'id': e.id,
        'data_evento': e.data_evento.strftime('%d/%m/%Y'),
        'tipo_evento': e.tipo_evento.nome if e.tipo_evento else 'N/A',
        'lote': e.lote.nome if e.lote else 'Lote Excluído', # Lida com lote órfão
        'tanque_origem': e.tanque_origem.nome if e.tanque_origem else '-',
        'tanque_destino': e.tanque_destino.nome if e.tanque_destino else '-',
        'quantidade': f'{e.quantidade:.2f}' if e.quantidade is not None else '-',
        'peso_medio': f'{e.peso_medio:.2f}' if e.peso_medio is not None else '-',
        'observacoes': e.observacoes or ''
    } for e in eventos]
    
    return JsonResponse({'success': True, 'eventos': data})

@login_required
@permission_required('producao.view_arracoamentosugerido', raise_exception=True)
def arracoamento_diario_view(request):
    """
    Renderiza a página de arraçoamento diário.
    """
    context = {
        'today': timezone.now().date(),
        'data_page': 'arracoamento-diario',
        'data_tela': 'arracoamento_diario',
    }
    return render_ajax_or_base(request, 'producao/arracoamento_diario.html', context)


@login_required
@require_http_methods(["GET"])
def api_linhas_producao_list(request):
    linhas = LinhaProducao.objects.all().order_by('nome')
    data = [{'id': l.id, 'nome': l.nome} for l in linhas]
    return JsonResponse(data, safe=False)

@login_required
@require_http_methods(["GET"])
def api_fases_com_tanques(request):
    """
    Retorna uma lista de fases de produção, cada uma contendo uma lista de tanques associados.
    """
    fases = FaseProducao.objects.all().order_by('nome')
    data = []
    for fase in fases:
        tanques_da_fase = Tanque.objects.filter(fase=fase).order_by('nome')
        tanques_data = [{'id': tanque.id, 'nome': tanque.nome} for tanque in tanques_da_fase]
        data.append({
            'id': fase.id,
            'nome': fase.nome,
            'tanques': tanques_data
        })
    return JsonResponse(data, safe=False)

@login_required
@require_http_methods(["GET"])  # Garante que a view só aceite requisições GET
def reprocessar_lotes_view(request):
    ctx = {
        "lotes": Lote.objects.all().order_by("-id")[:500],
        "tanques": Tanque.objects.all().order_by("nome"),
        "data_page": "producao-reprocessar-lotes", # Adicionado para consistência
    }
    return render_ajax_or_base(request, "producao/reprocessar_lotes.html", ctx)

@login_required
@require_POST
def reprocessar_lotes_api(request):
    """
    Reprocessa os dados de um lote a partir de uma data de início.
    - `dry_run`: Simula a execução sem salvar no banco.
    - `reprojetar`: Ativa a reprojeção do ciclo de vida a partir da data de início.
    - `forcar`: Força o recálculo de dias sem arraçoamento, usando o peso do dia anterior.
    """
    try:
        # 1. Leitura e Validação dos Parâmetros
        lote_id = int(request.POST.get("lote_id") or 0)
        data_inicio = request.POST.get("data_ini")
        data_fim = request.POST.get("data_fim") or None
        dry_run = request.POST.get("dry_run") in ("on", "true", "1")
        reprojetar = request.POST.get("reprojetar") in ("on", "true", "1")
        forcar = request.POST.get("forcar") in ("on", "true", "1")

        if not lote_id or not data_inicio:
            return JsonResponse({"ok": False, "message": "Lote e data de início são obrigatórios."}, status=400)

        start = datetime.strptime(data_inicio, "%Y-%m-%d").date()
        end = datetime.strptime(data_fim, "%Y-%m-%d").date() if data_fim else None
        lote = Lote.objects.get(pk=lote_id)

        # 2. Setup do Log
        linhas = []
        from control.utils import get_current_tenant
        current_tenant = get_current_tenant()
        if current_tenant:
            linhas.append(f"DEBUG: Tenant ativo: {current_tenant.slug}, DB: {current_tenant.db_name}")
        else:
            linhas.append("DEBUG: Nenhum tenant ativo. Usando DB 'default'.")
        linhas.append(f"Reprocessamento: lote={lote_id} start={start} end={end or '(até o fim)'}")
        linhas.append(f"Modo: {'SIMULACAO' if dry_run else 'EXECUCAO'} | reprojetar={reprojetar} | forcar={forcar}")
        linhas.append("-" * 80)

        # 3. Limpeza de Dados Futuros (se forçar e reprojetar)
        # REMOVIDO: Lógica de limpeza de LoteDiario para evitar perda de dados.
        # A reprojeção agora sobrescreve apenas os campos projetados, mantendo os reais intactos.

        # 4. Loop Principal de Reprocessamento (Dia a Dia)
        qs = LoteDiario.objects.filter(lote_id=lote_id, data_evento__gte=start).order_by("data_evento")
        if end:
            qs = qs.filter(data_evento__lte=end)

        # Pega o último dia válido ANTES da data de início como base para o primeiro dia do loop.
        # Prioriza dados reais, senão usa projetados. Se não houver LoteDiario anterior, usa dados do Lote.
        prev_ld_base = LoteDiario.objects.filter(
            lote_id=lote_id,
            data_evento__lt=start
        ).order_by("-data_evento").first()

        if prev_ld_base:
            # Usa os valores reais se existirem, senão os projetados do dia anterior
            prev_quantidade = prev_ld_base.quantidade_real if prev_ld_base.quantidade_real is not None else prev_ld_base.quantidade_projetada
            prev_peso_medio = prev_ld_base.peso_medio_real if prev_ld_base.peso_medio_real is not None else prev_ld_base.peso_medio_projetado
        else:
            # Se não há LoteDiario anterior, usa os dados iniciais do próprio Lote
            prev_quantidade = lote.quantidade_inicial
            prev_peso_medio = lote.peso_medio_inicial
        
        # Garante que os valores base não são None
        prev_quantidade = prev_quantidade or Decimal('0')
        prev_peso_medio = prev_peso_medio or Decimal('0')

        # O loop principal que processa cada dia a partir da data de início
        for ld in qs:
            # Define os valores iniciais do dia com base no estado final do dia anterior (prev_quantidade, prev_peso_medio)
            ld.quantidade_inicial = prev_quantidade
            ld.peso_medio_inicial = prev_peso_medio
            ld.biomassa_inicial = calc_biomassa_kg(ld.quantidade_inicial, ld.peso_medio_inicial)

            tem_realizado = ld.realizacoes.exists()

            if tem_realizado:
                recalcular_lote_diario_real(ld, request.user, commit=(not dry_run))
                linhas.append(f"[{ld.data_evento}] Recalculado com arraçoamento. Qtd Real: {ld.quantidade_real:.2f}, Peso Real: {ld.peso_medio_real:.2f}g")
            
            elif forcar:
                # Apura a quantidade real (considerando mortalidades/transferências do dia)
                ld.quantidade_real = _apurar_quantidade_real_no_dia(ld)
                
                # Como não há arraçoamento, não há crescimento. O peso se mantém.
                ld.peso_medio_real = ld.peso_medio_inicial
                ld.biomassa_real = calc_biomassa_kg(ld.quantidade_real, ld.peso_medio_real)
                ld.gpd_real = Decimal('0')
                
                # Zera campos de ração
                ld.racao_realizada = None
                ld.racao_realizada_kg = Decimal('0')
                ld.gpt_real = Decimal('0')
                ld.conversao_alimentar_real = None

                # Se forçamos o recálculo de um dia real, o projetado para ESSE dia deve ser igual.
                ld.quantidade_projetada = ld.quantidade_real
                ld.peso_medio_projetado = ld.peso_medio_real
                ld.biomassa_projetada = ld.biomassa_real
                ld.gpd_projetado = ld.gpd_real

                if not dry_run:
                    ld.save() # Salva todos os campos atualizados

                linhas.append(f"[{ld.data_evento}] Forçado recálculo sem arraçoamento. Qtd: {ld.quantidade_real:.2f}, Peso: {ld.peso_medio_real:.2f}g")

            else: # Dia sem arraçoamento e sem "Forçar". Apenas pula.
                linhas.append(f"[{ld.data_evento}] SKIP (sem arraçoamento realizado e sem forçar)")
                # Se pulou, os valores reais do dia anterior continuam sendo a base para o próximo dia.
                # Não atualizamos prev_quantidade e prev_peso_medio com os valores de ld,
                # pois ld não foi processado como "real".
                # No entanto, para a reprojeção, precisamos que os valores projetados sejam consistentes.
                # Se não há real, o projetado deve ser o que foi calculado na reprojeção.
                # Para o próximo dia, a base deve ser o que foi projetado para o dia atual.
                prev_quantidade = ld.quantidade_projetada if ld.quantidade_projetada is not None else prev_quantidade
                prev_peso_medio = ld.peso_medio_projetado if ld.peso_medio_projetado is not None else prev_peso_medio
                continue # Pula para a próxima iteração sem atualizar prev_quantidade/peso com valores reais de ld

            # Atualiza prev_quantidade e prev_peso_medio com os valores REAIS calculados para o dia atual
            # Isso garante que o próximo dia comece com a base correta.
            prev_quantidade = ld.quantidade_real
            prev_peso_medio = ld.peso_medio_real

        # 5. Reprojeção Final (se ativada)
        # Esta é a única chamada de reprojeção, garantindo um fluxo de dados limpo.
        if reprojetar and not dry_run:
            # A base para a reprojeção é o último dia ANTES da data de início.
            # Se não houver, a função `reprojetar_ciclo_de_vida` usará os dados do próprio lote.
            baseline_ld = LoteDiario.objects.filter(lote=lote, data_evento__lt=start).order_by("-data_evento").first()

            # (opcional, mas recomendado) garante que baseline esteja “fresco”
            if baseline_ld:
                recalcular_lote_diario_real(baseline_ld, request.user, commit=True)
                baseline_ld.refresh_from_db()

            reprojetar_ciclo_de_vida(
                lote=lote,
                data_de_inicio=start,
                quantidade_base_override=None,
                peso_base_g_override=None,
                ultimo_ld_override=baseline_ld  # ✅ base correta: dia anterior ao start
            )
            linhas.append("Reprojeção concluída.")

            # Log para verificação dos novos valores projetados
            reprojected_qs = LoteDiario.objects.filter(lote_id=lote_id, data_evento__gte=start).order_by("data_evento")
            linhas.append("\n--- Verificação de Valores Projetados (após reprojeção) ---")
            for r_ld in reprojected_qs[:10]: # Limita o log para não ser excessivo
                linhas.append(
                    f"[{r_ld.data_evento}] "
                    f"Qtd Proj: {r_ld.quantidade_projetada:.2f}, Peso Proj: {r_ld.peso_medio_projetado:.2f}g | "
                    f"Qtd Real: {r_ld.quantidade_real or 'N/A'}, Peso Real: {r_ld.peso_medio_real or 'N/A'}"
                )

        return JsonResponse({"ok": True, "dry_run": dry_run, "log": "\n".join(linhas)})

    except Lote.DoesNotExist:
        return JsonResponse({"ok": False, "message": "Lote não encontrado."}, status=404)
    except Exception as e:
        # Adiciona logging para depuração no servidor
        logging.exception("Erro em reprocessar_lotes_api")
        return JsonResponse({"ok": False, "message": f"Erro inesperado: {str(e)}"}, status=500)
