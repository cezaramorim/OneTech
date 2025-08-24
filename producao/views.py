import json
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.db import transaction
import pandas as pd
from io import BytesIO
from datetime import time
from django.contrib.auth.decorators import login_required, permission_required
from accounts.utils.decorators import login_required_json
from django.views.decorators.http import require_http_methods # Added import
from .serializers import TanqueSerializer # Import the serializer

from .models import (
    Tanque, CurvaCrescimento, CurvaCrescimentoDetalhe, Lote, 
    EventoManejo, AlimentacaoDiaria, Unidade, Malha, TipoTela,
    FaseProducao, TipoTanque, LinhaProducao, StatusTanque, Atividade
)
from .forms import (
    TanqueForm, CurvaCrescimentoForm, CurvaCrescimentoDetalheForm, ImportarCurvaForm, LoteForm, 
    EventoManejoForm, AlimentacaoDiariaForm, TanqueImportForm,
    UnidadeForm, MalhaForm, TipoTelaForm, LinhaProducaoForm, FaseProducaoForm,
    StatusTanqueForm, TipoTanqueForm, AtividadeForm
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
    app_messages = get_app_messages(request)
    template = 'producao/tanques/importar_tanques.html'
    redirect_url = reverse('producao:lista_tanques')

    if request.method == 'POST':
        form = TanqueImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                df = pd.read_excel(request.FILES['arquivo_excel'])
                # Normaliza nomes das colunas
                df.columns = [c.strip().lower() for c in df.columns]
                
                required_cols = ['nome', 'unidade', 'linha_producao', 'fase', 'tipo_tanque', 'status_tanque', 'malha']
                if not all(col in df.columns for col in required_cols):
                    raise ValueError("Colunas obrigatórias não encontradas. Verifique o template.")

                # Contadores para a mensagem de sucesso
                created_count = 0
                updated_count = 0

                with transaction.atomic():
                    for index, row in df.iterrows():
                        # Busca ou cria objetos relacionados
                        unidade, _ = Unidade.objects.get_or_create(nome__iexact=row['unidade'], defaults={'nome': row['unidade']})
                        linha, _ = LinhaProducao.objects.get_or_create(nome__iexact=row['linha_producao'], defaults={'nome': row['linha_producao']})
                        fase, _ = FaseProducao.objects.get_or_create(nome__iexact=row['fase'], defaults={'nome': row['fase']})
                        tipo, _ = TipoTanque.objects.get_or_create(nome__iexact=row['tipo_tanque'], defaults={'nome': row['tipo_tanque']})
                        status, _ = StatusTanque.objects.get_or_create(nome__iexact=row['status_tanque'], defaults={'nome': row['status_tanque']})
                        malha, _ = Malha.objects.get_or_create(nome__iexact=row['malha'], defaults={'nome': row['malha']})

                        # Calcula campos dimensionais
                        largura_val = _to_decimal(row.get('largura', None))
                        comprimento_val = _to_decimal(row.get('comprimento', None))
                        profundidade_val = _to_decimal(row.get('profundidade', None))

                        mq = None
                        mc = None
                        ha = None

                        if largura_val is not None and comprimento_val is not None:
                            mq = largura_val * comprimento_val
                        if mq is not None and profundidade_val is not None:
                            mc = mq * profundidade_val
                        if mq is not None:
                            ha = mq / Decimal("10000")

                        # Atualiza ou cria o tanque
                        tanque, created = Tanque.objects.update_or_create(
                            nome=row['nome'], # Campo de busca
                            defaults={
                                'unidade': unidade,
                                'linha_producao': linha,
                                'fase': fase,
                                'tipo_tanque': tipo,
                                'status_tanque': status,
                                'largura': _to_decimal(row.get('largura', None)),
                                'comprimento': _to_decimal(row.get('comprimento', None)),
                                'profundidade': _to_decimal(row.get('profundidade', None)),
                                'sequencia': row.get('sequencia', 0),
                                'tag_tanque': str(row.get('tag_tanque', '')).strip() if pd.notna(row.get('tag_tanque', '')) else '',
                                'malha': malha,
                                'metro_quadrado': mq,
                                'metro_cubico': mc,
                                'ha': ha,
                                # Adicione outros campos opcionais aqui
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


# === Alimentação Diária ===

class ListaAlimentacaoView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = AlimentacaoDiaria
    template_name = 'producao/alimentacao/lista_alimentacao.html'
    context_object_name = 'alimentacoes'
    permission_required = 'producao.view_alimentacaodiaria'
    raise_exception = True

    def get_queryset(self):
        qs = super().get_queryset()
        termo = self.request.GET.get('termo_alimentacao', '').strip()
        if termo:
            qs = qs.filter(
                Q(lote__nome__icontains=termo) |
                Q(produto_racao__nome__icontains=termo)
            )
        return qs

    def render_to_response(self, context, **response_kwargs):
        context['termo_busca'] = self.request.GET.get('termo_alimentacao', '').strip()
        return render_ajax_or_base(self.request, self.template_name, context)


class RegistrarAlimentacaoView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = AlimentacaoDiaria
    form_class = AlimentacaoDiariaForm
    template_name = 'producao/alimentacao/registrar_alimentacao.html'
    success_url = reverse_lazy('producao:lista_alimentacao')
    permission_required = 'producao.add_alimentacaodiaria'
    raise_exception = True

    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)


class EditarAlimentacaoView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = AlimentacaoDiaria
    form_class = AlimentacaoDiariaForm
    template_name = 'producao/alimentacao/editar_alimentacao.html'
    success_url = reverse_lazy('producao:lista_alimentacao')
    permission_required = 'producao.change_alimentacaodiaria'
    raise_exception = True

    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)


class ExcluirAlimentacaoMultiplaView(BulkDeleteView):
    model = AlimentacaoDiaria
    permission_required = 'producao.delete_alimentacaodiaria'
    success_url_name = 'producao:lista_alimentacao'


from django.forms.models import model_to_dict
from decimal import Decimal

def _to_decimal(s):
    if s is None: return None
    s = str(s).strip().replace('.', '').replace(',', '.')
    try: return Decimal(s)
    except: return None

@login_required_json
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
    return JsonResponse(d, safe=False)

@login_required_json
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
    for campo in ("unidade","fase","tipo_tanque","linha_producao","malha","status_tanque"):
        v = request.POST.get(f"{campo}")
        if v: setattr(obj, f"{campo}_id", int(v))

    ativo = request.POST.get("ativo")
    if ativo is not None:
        obj.ativo = ativo in ("1","true","True","on","True")

    obj.save()
    return JsonResponse({"success": True, "message": "Tanque atualizado com sucesso.", "id": obj.id})

@login_required_json
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
    mc = _to_decimal(request.POST.get("metro_cubico"))
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
    for campo in ("unidade","fase","tipo_tanque","linha_producao","malha","status_tanque"):
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

from django.views.decorators.http import require_http_methods

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
        "hora_inicio": d.hora_inicio.strftime("%H:%M") if getattr(d, "hora_inicio", None) else None,
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

@login_required_json
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

@login_required_json
@require_http_methods(["GET"])
@permission_required('producao.view_curvacrescimento', raise_exception=True)
def detalhe_view(request, curva_id: int, detalhe_id: int):
    """
    GET /producao/api/curva/<id>/detalhes/<detalhe_id>/
    """
    curva = get_object_or_404(CurvaCrescimento, pk=curva_id)
    detalhe = get_object_or_404(CurvaCrescimentoDetalhe, pk=detalhe_id, curva=curva)
    return JsonResponse(serialize_detalhe(detalhe), status=200)

@login_required_json
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

@login_required_json
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

@login_required_json
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

@login_required_json
@require_http_methods(["POST"])
@permission_required('producao.change_curvacrescimentodetalhe', raise_exception=True)
@transaction.atomic
def detalhe_update_view(request, curva_id: int, detalhe_id: int):
    """
    POST /producao/api/curva/<id>/detalhes/<detalhe_id>/
    """
    curva = get_object_or_404(CurvaCrescimento, pk=curva_id)
    detalhe = get_object_or_404(CurvaCrescimentoDetalhe, pk=detalhe_id, curva=curva)
    form = CurvaCrescimentoDetalheForm(request.POST, instance=detalhe)
    if form.is_valid():
        detalhe = form.save()
        return JsonResponse({
            "success": True,
            "message": "Período atualizado.",
            "periodo": serialize_detalhe(detalhe)
        }, status=200)
    return JsonResponse({"success": False, "errors": form.errors, "message": "Erro ao atualizar período."}, status=400)

