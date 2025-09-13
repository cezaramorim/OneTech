import json
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.utils import timezone
import pandas as pd
from io import BytesIO
from datetime import time
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods
import logging

# Configuração básica de logging para exibir mensagens no console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from .models import (
    Tanque, CurvaCrescimento, CurvaCrescimentoDetalhe, Lote, 
    EventoManejo, Unidade, Malha, TipoTela,
    FaseProducao, TipoTanque, LinhaProducao, StatusTanque, Atividade
)
from .forms import (
    TanqueForm, CurvaCrescimentoForm, CurvaCrescimentoDetalheForm, ImportarCurvaForm, LoteForm, 
    EventoManejoForm, TanqueImportForm,
    UnidadeForm, MalhaForm, TipoTelaForm, LinhaProducaoForm, FaseProducaoForm,
    StatusTanqueForm, TipoTanqueForm, AtividadeForm, PovoamentoForm
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
        qs = super().get_queryset()
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

# === Eventos de Manejo ===

class ListaEventosView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = EventoManejo
    template_name = 'producao/eventos/lista_eventos.html'
    context_object_name = 'eventos'
    permission_required = 'producao.view_eventomanejo'
    raise_exception = True

    def get_queryset(self):
        qs = super().get_queryset()
        termo = self.request.GET.get('termo_evento', '').strip()
        if termo:
            qs = qs.filter(
                Q(tipo_evento__icontains=termo) |
                Q(lote__nome__icontains=termo)
            )
        return qs

    def render_to_response(self, context, **response_kwargs):
        context['termo_busca'] = self.request.GET.get('termo_evento', '').strip()
        return render_ajax_or_base(self.request, self.template_name, context)


class RegistrarEventoView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = EventoManejo
    form_class = EventoManejoForm
    template_name = 'producao/eventos/registrar_evento.html'
    success_url = reverse_lazy('producao:lista_eventos')
    permission_required = 'producao.add_eventomanejo'
    raise_exception = True

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
        'data_tela': 'gerenciar_tanques',
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
        'data_tela': 'gerenciar_curvas',
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
                        primeiro_erro = next(iter(form.errors.values()))[0]
                        return JsonResponse({'success': False, 'message': f'Erro na validação: {primeiro_erro}'}, status=400)

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
                            lote_existente.recalcular_estado_atual()

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
                        novo_lote.recalcular_estado_atual()

                        # --- INÍCIO DA NOVA INTEGRAÇÃO ---
                        from .utils import projetar_ciclo_de_vida_lote
                        import logging
                        try:
                            projetar_ciclo_de_vida_lote(novo_lote)
                        except Exception as e:
                            # Logar o erro de projeção, mas não impedir o sucesso do povoamento.
                            # É crucial que o povoamento não falhe se a projeção tiver um problema.
                            logging.error(f"Erro ao projetar o ciclo de vida para o novo lote {novo_lote.id}: {e}")
                        # --- FIM DA NOVA INTEGRAÇÃO ---
            
            success_message = app_messages.success_process(f'{len(povoamentos)} povoamento(s) processado(s) com sucesso!')
            return JsonResponse({'success': True, 'message': success_message})

        except Exception as e:
            error_message = app_messages.error(f'Ocorreu um erro inesperado: {e}')
            return JsonResponse({'success': False, 'message': error_message}, status=500)

    # Prepara dados enriquecidos para o frontend
    tanques = Tanque.objects.select_related('status_tanque').order_by('nome')
    lotes_ativos_tanque_ids = set(Lote.objects.filter(ativo=True, tanque_atual__isnull=False).values_list('tanque_atual_id', flat=True))

    tanques_data = []
    for tanque in tanques:
        tanques_data.append({
            'pk': tanque.pk,
            'nome': tanque.nome,
            'status_nome': tanque.status_tanque.nome.lower() if tanque.status_tanque else '',
            'tem_lote_ativo': tanque.pk in lotes_ativos_tanque_ids
        })

    context = {
        'curvas': CurvaCrescimento.objects.order_by('nome'),
        'tanques_json': json.dumps(tanques_data),
        'fases': list(FaseProducao.objects.values('pk', 'nome')),
        'linhas': list(LinhaProducao.objects.values('pk', 'nome')),
        'tipos_evento': EventoManejo.TIPO_EVENTO_CHOICES, # Adiciona os tipos de evento
        'data_page': 'povoamento-lotes'
    }
    return render_ajax_or_base(request, 'producao/povoamento_lotes.html', context)

@login_required
def historico_povoamento_view(request):
    """Filtra e retorna o histórico de eventos de manejo."""
    try:
        # Filtros da query string
        data_inicial = request.GET.get('data_inicial')
        data_final = request.GET.get('data_final')
        status = request.GET.get('status') # Retrieve the status parameter

        eventos = EventoManejo.objects.select_related(
            'lote', 'tanque_destino'
        ).order_by('-data_evento', '-id')

        if data_inicial:
            eventos = eventos.filter(data_evento__gte=data_inicial)
        if data_final:
            eventos = eventos.filter(data_evento__lte=data_final)
        
        # Add the status filter
        if status:
            eventos = eventos.filter(tipo_evento=status)

        eventos = eventos[:100] # Limita a 100 registros para performance

        data = [
            {
                'id': evento.id,
                'data': evento.data_evento.strftime('%d/%m/%Y'),
                'lote': evento.lote.nome,
                'tanque': evento.tanque_destino.nome if evento.tanque_destino else 'N/A',
                'quantidade': f'{evento.quantidade:,.2f}'.replace(',', ' ').replace('.', ',').replace(' ', '.'),
                'peso_medio': f'{evento.peso_medio:,.2f}'.replace(',', ' ').replace('.', ',').replace(' ', '.'),
                'tipo_evento': evento.get_tipo_evento_display(),
            }
            for evento in eventos
        ]

        return JsonResponse({'success': True, 'historico': data})

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao buscar histórico: {e}'}, status=500)
    
@login_required
@require_http_methods(["GET"])
def get_active_lote_for_tanque_api(request, tanque_id):
    """
    API endpoint para buscar o lote ativo de um tanque específico.
    Retorna o nome e ID do lote se encontrado.
    """
    try:
        lote = Lote.objects.get(tanque_atual_id=tanque_id, ativo=True)
        return JsonResponse({'success': True, 'lote': {'id': lote.id, 'nome': lote.nome}})
    except Lote.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Nenhum lote ativo encontrado.'}, status=404)
    except Lote.MultipleObjectsReturned:
        return JsonResponse({'success': False, 'message': 'Múltiplos lotes ativos encontrados.'}, status=409) # 409 Conflict


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
        'ultimos_eventos': ultimos_eventos,
        'data_page': 'gerenciar-eventos',
        'data_tela': 'gerenciar_eventos',
    }
    return render_ajax_or_base(request, 'producao/eventos/gerenciar_eventos.html', context)

@login_required
@require_http_methods(["GET"])
@permission_required('producao.view_lote', raise_exception=True)
def get_lotes_ativos_api(request):
    lotes = Lote.objects.filter(ativo=True).select_related(
        'tanque_atual__unidade', 
        'tanque_atual__linha_producao', 
        'fase_producao'
    ).order_by('tanque_atual__nome')
    
    # Filtros
    unidade_id = request.GET.get('unidade')
    linha_id = request.GET.get('linha_producao')
    fase_id = request.GET.get('fase_producao')
    tanque_nome = request.GET.get('tanque')

    if unidade_id:
        lotes = lotes.filter(tanque_atual__unidade_id=unidade_id)
    if linha_id:
        lotes = lotes.filter(tanque_atual__linha_producao_id=linha_id)
    if fase_id:
        lotes = lotes.filter(fase_producao_id=fase_id)
    if tanque_nome:
        lotes = lotes.filter(tanque_atual__nome__icontains=tanque_nome)

    data = {
        'lotes': [
            {
                'lote_id': lote.id,
                'lote_nome': lote.nome,
                'tanque_id': lote.tanque_atual.id if lote.tanque_atual else None,
                'tanque_nome': lote.tanque_atual.nome if lote.tanque_atual else 'N/A',
                'data_inicio': lote.data_povoamento,
                'qtd_atual': lote.quantidade_atual,
                'peso_medio_atual': lote.peso_medio_atual,
                'biomassa_atual': lote.biomassa_atual,
            }
            for lote in lotes
        ]
    }
    return JsonResponse(data)


@login_required
@require_http_methods(["GET"])
@permission_required('producao.view_eventomanejo', raise_exception=True)
def api_ultimos_eventos(request):
    try:
        offset = int(request.GET.get('offset', 0))
        limit = 20

        # Filtros
        termo = request.GET.get('termo', '').strip()
        unidade_id = request.GET.get('unidade')
        linha_id = request.GET.get('linha_producao')
        fase_id = request.GET.get('fase')
        
        eventos = EventoManejo.objects.select_related(
            'lote__tanque_atual', 'tanque_origem', 'tanque_destino'
        ).order_by('-data_evento', '-id')

        if termo:
            eventos = eventos.filter(
                Q(lote__nome__icontains=termo) |
                Q(tanque_origem__nome__icontains=termo) |
                Q(tanque_destino__nome__icontains=termo) |
                Q(tipo_evento__icontains=termo)
            )
        
        # Aplica filtros de dropdown se eles forem fornecidos e não forem "todos"
        if unidade_id and unidade_id.lower() not in ['', 'todas', 'todos']:
            # Filtra baseado no tanque de origem OU no tanque do lote
            eventos = eventos.filter(
                Q(lote__tanque_atual__unidade_id=unidade_id) | Q(tanque_origem__unidade_id=unidade_id)
            )
        if linha_id and linha_id.lower() not in ['', 'todas', 'todos']:
            eventos = eventos.filter(
                Q(lote__tanque_atual__linha_producao_id=linha_id) | Q(tanque_origem__linha_producao_id=linha_id)
            )
        if fase_id and fase_id.lower() not in ['', 'todas', 'todos']:
            eventos = eventos.filter(lote__fase_producao_id=fase_id)

        eventos = eventos.distinct()[offset:offset+limit]

        data = [
            {
                'id': evento.id,
                'data_evento': evento.data_evento.strftime('%d/%m/%Y'),
                'tipo_evento': evento.get_tipo_evento_display(),
                'lote': evento.lote.nome if evento.lote else 'N/A',
                'tanque_origem': evento.tanque_origem.nome if evento.tanque_origem else 'N/A',
                'tanque_destino': evento.tanque_destino.nome if evento.tanque_destino else 'N/A',
                'quantidade': f'{evento.quantidade:,.2f}'.replace(',', ' ').replace('.', ',').replace(' ', '.') if evento.quantidade is not None else '-',
                'peso_medio': f'{evento.peso_medio:,.2f}'.replace(',', ' ').replace('.', ',').replace(' ', '.') if evento.peso_medio is not None else '-',
                'observacoes': evento.observacoes or ''
            }
            for evento in eventos
        ]
        
        return JsonResponse({'success': True, 'eventos': data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao buscar eventos: {e}'}, status=500)


@login_required
@require_http_methods(["POST"])
@permission_required('producao.add_eventomanejo', raise_exception=True)
@transaction.atomic
def registrar_mortalidade_api(request):
    app_messages = get_app_messages(request)
    try:
        data = json.loads(request.body)
        lancamentos = data.get('lancamentos', [])

        if not lancamentos:
            message = app_messages.error("Nenhum lançamento recebido.")
            return JsonResponse({'success': False, 'message': message}, status=400)

        for item in lancamentos:
            lote = get_object_or_404(Lote, pk=item['lote_id'])
            EventoManejo.objects.create(
                tipo_evento='Mortalidade',
                lote=lote,
                tanque_origem=lote.tanque_atual,
                tanque_destino=None,
                data_evento=item['data_evento'],
                quantidade=item['quantidade'],
                peso_medio=item['peso_medio']
            )
        
        message = app_messages.success_process(f'{len(lancamentos)} lançamento(s) de mortalidade registrado(s) com sucesso.')
        return JsonResponse({'success': True, 'message': message})
    except Exception as e:
        message = app_messages.error(f'Erro ao registrar mortalidade: {str(e)}')
        return JsonResponse({'success': False, 'message': message}, status=400)

@login_required
@require_http_methods(["POST"])
@permission_required('producao.add_eventomanejo', raise_exception=True)
@transaction.atomic
def processar_mortalidade_api(request):
    app_messages = get_app_messages(request)
    try:
        data = json.loads(request.body)
        lancamentos = data.get('lancamentos', [])
        data_evento_str = data.get('data_evento')

        if not lancamentos:
            message = app_messages.error("Nenhum lançamento de mortalidade recebido para processar.")
            return JsonResponse({'success': False, 'message': message}, status=400)

        # Converter a string da data para um objeto date
        try:
            data_evento = datetime.strptime(data_evento_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            message = app_messages.error("Formato de data inválido.")
            return JsonResponse({'success': False, 'message': message}, status=400)

        processed_count = 0
        for item in lancamentos:
            lote_id = item.get('lote_id')
            quantidade_mortalidade = item.get('quantidade_mortalidade')
            biomassa_retirada = item.get('biomassa_retirada')

            if not lote_id or quantidade_mortalidade is None:
                continue

            lote = get_object_or_404(Lote, pk=lote_id)

            EventoManejo.objects.create(
                tipo_evento='Mortalidade',
                lote=lote,
                tanque_origem=lote.tanque_atual,
                tanque_destino=None,
                data_evento=data_evento, # <--- USAR A DATA DO USUÁRIO AQUI
                quantidade=quantidade_mortalidade,
                peso_medio=lote.peso_medio_atual,
                observacoes=f"Mortalidade registrada. Biomassa retirada: {biomassa_retirada:.2f} kg.",
                tipo_movimento='Morte' # <--- Adicionar esta linha
            )

            lote.recalcular_estado_atual()
            processed_count += 1
        
        message = app_messages.success_process(f'{processed_count} lançamento(s) de mortalidade processado(s) com sucesso.')
        return JsonResponse({'success': True, 'message': message})

    except json.JSONDecodeError:
        message = app_messages.error("Requisição inválida: JSON malformado.")
        return JsonResponse({'success': False, 'message': message}, status=400)
    except Exception as e:
        message = app_messages.error(f'Erro ao processar lançamentos de mortalidade: {str(e)}')
        return JsonResponse({'success': False, 'message': message}, status=400)

# producao/views.py
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, F, Value, IntegerField
from django.db.models.functions import Coalesce

@login_required
def api_mortalidade_lotes_ativos(request):
    """
    Retorna tanques com lotes ativos na data informada, aplicando filtros de
    unidade/linha/fase. Considera 'ativo' se data_inicio <= data_ref e
    (data_baixa IS NULL ou data_baixa >= data_ref).
    """
    # Import local: evita ciclos (producao.views <-> producao.models etc.)
    from .models import Lote  # ajuste se seu model tiver outro nome/caminho

    def _parse_data(s):
        if not s:
            return None
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                pass
        return None

    def _not_all(v):
        if not v:
            return False
        vl = str(v).strip().lower()
        return vl not in ("todas", "todos", "")

    unidade_id = request.GET.get("unidade")
    linha_id   = request.GET.get("linha_producao")
    fase_id    = request.GET.get("fase")
    data_str   = request.GET.get("data")
    termo      = request.GET.get("termo", '').strip()

    data_ref = _parse_data(data_str) or datetime.today().date()

    # Base: lotes ativos
    qs = (Lote.objects
          .select_related("tanque_atual", "tanque_atual__unidade", "tanque_atual__linha_producao", "tanque_atual__fase")
          .filter(ativo=True, quantidade_atual__gt=0)
    )

    if _not_all(unidade_id):
        qs = qs.filter(tanque_atual__unidade_id=unidade_id)
    if _not_all(linha_id):
        qs = qs.filter(tanque_atual__linha_producao_id=linha_id)
    if _not_all(fase_id):
        qs = qs.filter(tanque_atual__fase_id=fase_id)
    
    if termo:
        qs = qs.filter(Q(nome__icontains=termo) | Q(tanque_atual__nome__icontains=termo))

    results = []
    for lote in qs.order_by("tanque_atual__nome", "id"):
        peso_medio_g = float(lote.peso_medio_atual or 0)
        qtd_atual    = int(lote.quantidade_atual or 0)
        biomassa_kg  = (peso_medio_g / 1000.0) * qtd_atual

        results.append({
            "tanque": getattr(lote.tanque_atual, "nome", str(lote.tanque_atual_id)),
            "lote_id": lote.id,
            "lote": lote.nome,
            "data_inicio": lote.data_povoamento.strftime("%d/%m/%Y") if lote.data_povoamento else "",
            "qtd_atual": qtd_atual,
            "peso_medio_g": round(peso_medio_g, 2),
            "biomassa_kg": round(biomassa_kg, 2),
            # campos do dia (para usuário preencher na UI)
            "qtd_mortalidade": 0,
            "peso_medio_dia_g": "-",
            "biomassa_mort_kg": 0.00,
        })

    return JsonResponse({"results": results})


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
    """
    Retorna uma lista de linhas de produção em formato JSON.
    """
    linhas = LinhaProducao.objects.all().values('id', 'nome').order_by('nome')
    return JsonResponse(list(linhas), safe=False)