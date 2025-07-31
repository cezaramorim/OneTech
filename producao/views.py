import json
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.db import transaction
import pandas as pd
from io import BytesIO
from datetime import time
from django.contrib.auth.decorators import login_required, permission_required

from .models import (
    Tanque, CurvaCrescimento, CurvaCrescimentoDetalhe, Lote, 
    EventoManejo, AlimentacaoDiaria
)
from .forms import (
    TanqueForm, CurvaCrescimentoForm, ImportarCurvaForm, LoteForm, 
    EventoManejoForm, AlimentacaoDiariaForm
)
from .utils import AjaxFormMixin, BulkDeleteView
from common.utils import render_ajax_or_base
from common.messages_utils import get_app_messages
from produto.models import Produto

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
                    level = 'warning'
                else:
                    message = app_messages.success_imported(curva, source_type="Excel")
                    level = 'success'

                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'sucesso': True, 'message': message, 'redirect_url': redirect_url, 'level': level})
                return redirect(redirect_url)

            except Exception as e:
                error_message = f"Ocorreu um erro ao processar o arquivo: {e}"
                if "KeyError" in str(e):
                    error_message = "Verifique se todas as colunas obrigatórias estão presentes no arquivo Excel e com os nomes corretos."
                app_messages.error(error_message)
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'sucesso': False, 'message': error_message}, status=400)
                return render(request, template, {'form': form})
        else:
            # Form is invalid
            message = "Erro de validação. Verifique os campos do formulário."
            app_messages.error(message)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': False, 'message': message, 'erros': form.errors}, status=400)
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


# === API para Edição Interativa de Detalhes da Curva ===

class AtualizarDetalheCurvaAPIView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'producao.change_curvacrescimentodetalhe'
    raise_exception = True

    def post(self, request, *args, **kwargs):
        app_messages = get_app_messages(request)
        try:
            data = json.loads(request.body)
            detalhe_id = data.get('detalhe_id')
            racao_id = data.get('racao_id')
            fill_down = data.get('fill_down', False)

            if not detalhe_id:
                message = app_messages.error('ID do detalhe da curva não fornecido.')
                return JsonResponse({'sucesso': False, 'message': message}, status=400)

            detalhe = get_object_or_404(CurvaCrescimentoDetalhe, pk=detalhe_id)
            
            racao_obj = None
            if racao_id:
                racao_obj = get_object_or_404(Produto, pk=racao_id)
                if racao_obj.categoria and racao_obj.categoria.nome.lower() != 'ração':
                    message = app_messages.error('Produto selecionado não é uma ração.')
                    return JsonResponse({'sucesso': False, 'message': message}, status=400)
            
            with transaction.atomic():
                detalhe.racao = racao_obj
                detalhe.save()

                if fill_down:
                    CurvaCrescimentoDetalhe.objects.filter(
                        curva=detalhe.curva,
                        periodo_semana__gt=detalhe.periodo_semana
                    ).update(racao=racao_obj)
            
            message = app_messages.success_updated(detalhe, custom_message='Detalhe da curva atualizado com sucesso.')
            return JsonResponse({'sucesso': True, 'message': message})

        except json.JSONDecodeError:
            message = app_messages.error('Requisição JSON inválida.')
            return JsonResponse({'sucesso': False, 'message': message}, status=400)
        except Exception as e:
            message = app_messages.error(f'Erro ao atualizar detalhe da curva: {str(e)}')
            return JsonResponse({'sucesso': False, 'message': message}, status=500)