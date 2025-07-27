from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction
import pandas as pd
from io import BytesIO
from datetime import time

from .models import (
    Tanque, CurvaCrescimento, CurvaCrescimentoDetalhe, Lote, 
    EventoManejo, AlimentacaoDiaria
)
from .forms import (
    TanqueForm, CurvaCrescimentoForm, ImportarCurvaForm, LoteForm, 
    EventoManejoForm, AlimentacaoDiariaForm
)
from .utils import render_ajax_or_base, AjaxFormMixin, BulkDeleteView

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
                Q(linha_producao__nome__icontains=termo) |
                Q(tipo_tanque__nome__icontains=termo) |
                Q(atividade__nome__icontains=termo) |
                Q(status_tanque__nome__icontains=termo)
            )
        return qs

    def render_to_response(self, context, **response_kwargs):
        context['termo_busca'] = self.request.GET.get('termo_tanque', '').strip()
        return render_ajax_or_base(self.request, self.template_name, context)


class CadastrarTanqueView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, CreateView):
    model = Tanque
    form_class = TanqueForm
    template_name = 'producao/tanques/cadastrar_tanque.html'
    success_url = reverse_lazy('producao:lista_tanques')
    permission_required = 'producao.add_tanque'
    success_message = "Tanque cadastrado com sucesso!"
    raise_exception = True

    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)


class EditarTanqueView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = Tanque
    form_class = TanqueForm
    template_name = 'producao/tanques/editar_tanque.html'
    success_url = reverse_lazy('producao:lista_tanques')
    permission_required = 'producao.change_tanque'
    success_message = "Tanque atualizado com sucesso!"
    raise_exception = True

    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)


class ExcluirTanquesMultiplosView(BulkDeleteView):
    model = Tanque
    permission_required = 'producao.delete_tanque'
    success_url_name = 'producao:lista_tanques'


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
    success_message = "Curva de Crescimento cadastrada com sucesso!"
    raise_exception = True

    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)


class EditarCurvaView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = CurvaCrescimento
    form_class = CurvaCrescimentoForm
    template_name = 'producao/curvas/editar_curva.html'
    success_url = reverse_lazy('producao:lista_curvas')
    permission_required = 'producao.change_curvacrescimento'
    success_message = "Curva de Crescimento atualizada com sucesso!"
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
        context['detalhes'] = CurvaCrescimentoDetalhe.objects.filter(curva=self.object).order_by('periodo')
        return context

    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)


class ExcluirCurvasMultiplasView(BulkDeleteView):
    model = CurvaCrescimento
    permission_required = 'producao.delete_curvacrescimento'
    success_url_name = 'producao:lista_curvas'

# --- Views Funcionais para Curva (Lógica Customizada) ---

from django.contrib.auth.decorators import login_required, permission_required

@login_required
@permission_required('producao.add_curvacrescimento', raise_exception=True)
def importar_curva_view(request):
    if request.method == 'POST':
        form = ImportarCurvaForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    curva = form.save()
                    df = pd.read_excel(request.FILES['arquivo_excel'])
                    
                    col_mapping = {
                        'Período': 'periodo', 'Dias': 'dias_periodo', 'Peso Inicial': 'peso_inicial_g',
                        'Peso Final': 'peso_final_g', 'Ganho de Peso': 'ganho_peso_g', 'nº Tratos': 'tratos_diarios',
                        'Hora Início': 'hora_inicio_trato', '% Arraç. Biomassa': 'arracoamento_biomassa_perc',
                        '% Mortalidade Presumida': 'mortalidade_presumida_perc', 'Ração': 'tipo_racao',
                        'GPD': 'gpd', 'TCA': 'tca',
                    }
                    df.rename(columns=col_mapping, inplace=True)

                    for _, row in df.iterrows():
                        # ... (Lógica de conversão de hora e criação de detalhes) ...
                        CurvaCrescimentoDetalhe.objects.create(curva=curva, **row.to_dict())

                messages.success(request, "Curva de crescimento importada com sucesso!")
                return redirect('producao:lista_curvas')

            except Exception as e:
                messages.error(request, f"Ocorreu um erro ao processar o arquivo: {e}")
    else:
        form = ImportarCurvaForm()

    return render_ajax_or_base(request, 'producao/curvas/importar_curva.html', {'form': form})

@login_required
@permission_required('producao.add_curvacrescimento', raise_exception=True)
def download_template_curva_view(request):
    headers = [
        'Período', 'Dias', 'Peso Inicial', 'Peso Final', 'Ganho de Peso',
        'nº Tratos', 'Hora Início', '% Arraç. Biomassa',
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
    success_message = "Lote cadastrado com sucesso!"
    raise_exception = True

    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)


class EditarLoteView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = Lote
    form_class = LoteForm
    template_name = 'producao/lotes/editar_lote.html'
    success_url = reverse_lazy('producao:lista_lotes')
    permission_required = 'producao.change_lote'
    success_message = "Lote atualizado com sucesso!"
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
    success_message = "Evento de manejo registrado com sucesso!"
    raise_exception = True

    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)


class EditarEventoView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = EventoManejo
    form_class = EventoManejoForm
    template_name = 'producao/eventos/editar_evento.html'
    success_url = reverse_lazy('producao:lista_eventos')
    permission_required = 'producao.change_eventomanejo'
    success_message = "Evento de manejo atualizado com sucesso!"
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
    success_message = "Alimentação registrada com sucesso!"
    raise_exception = True

    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)


class EditarAlimentacaoView(LoginRequiredMixin, PermissionRequiredMixin, AjaxFormMixin, UpdateView):
    model = AlimentacaoDiaria
    form_class = AlimentacaoDiariaForm
    template_name = 'producao/alimentacao/editar_alimentacao.html'
    success_url = reverse_lazy('producao:lista_alimentacao')
    permission_required = 'producao.change_alimentacaodiaria'
    success_message = "Alimentação atualizada com sucesso!"
    raise_exception = True

    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)


class ExcluirAlimentacaoMultiplaView(BulkDeleteView):
    model = AlimentacaoDiaria
    permission_required = 'producao.delete_alimentacaodiaria'
    success_url_name = 'producao:lista_alimentacao'
