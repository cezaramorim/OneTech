import json
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
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
from .utils import AjaxFormMixin, BulkDeleteView
from common.utils import render_ajax_or_base

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

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.contrib import messages
from django.http import HttpResponse, JsonResponse # Adicionado JsonResponse
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
from .utils import AjaxFormMixin, BulkDeleteView
from common.utils import render_ajax_or_base

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
                Q(linha_producao__icontains=termo) |
                Q(tipo_tanque__icontains=termo) |
                Q(atividade__icontains=termo) |
                Q(status_tanque__icontains=termo)
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
        context['detalhes'] = CurvaCrescimentoDetalhe.objects.filter(curva=self.object).order_by('periodo_semana')
        return context

    def render_to_response(self, context, **response_kwargs):
        return render_ajax_or_base(self.request, self.template_name, context)


class ExcluirCurvasMultiplasView(BulkDeleteView):
    model = CurvaCrescimento
    permission_required = 'producao.delete_curvacrescimento'
    success_url_name = 'producao:lista_curvas'

# --- Views Funcionais para Curva (Lógica Customizada) ---

from django.contrib.auth.decorators import login_required, permission_required
from produto.models import Produto, CategoriaProduto # Importa Produto e CategoriaProduto

@login_required
@permission_required('producao.add_curvacrescimento', raise_exception=True)
def importar_curva_view(request):
    if request.method == 'POST':
        form = ImportarCurvaForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Cria o objeto CurvaCrescimento manualmente
                    curva = CurvaCrescimento.objects.create(
                        nome=form.cleaned_data['nome'],
                        especie=form.cleaned_data['especie'],
                        rendimento_perc=form.cleaned_data['rendimento_perc']
                    )
                    df = pd.read_excel(request.FILES['arquivo_excel'])
                    
                    # Mapeamento das colunas do Excel para os campos do modelo
                    col_mapping = {
                        'Período': 'periodo_semana',
                        'Dias': 'periodo_dias',
                        'Peso Inicial': 'peso_inicial',
                        'Peso Final': 'peso_final',
                        'Ganho de Peso': 'ganho_de_peso',
                        'Nº Tratos': 'numero_tratos',
                        'Hora Início': 'hora_inicio',
                        '% Arraç. Biomassa': 'arracoamento_biomassa_perc',
                        '% Mortalidade Presumida': 'mortalidade_presumida_perc',
                        'Ração': 'racao_nome', # Nome temporário para buscar o objeto Produto
                        'GPD': 'gpd',
                        'TCA': 'tca',
                    }
                    df.rename(columns=col_mapping, inplace=True)

                    # Lista para armazenar mensagens de rações não encontradas
                    racao_nao_encontrada_msgs = []

                    for index, row in df.iterrows():
                        racao_obj = None
                        racao_nome = row.get('racao_nome')
                        if racao_nome:
                            try:
                                # Busca a ração pelo nome e categoria 'Ração'
                                racao_obj = Produto.objects.get(nome__iexact=racao_nome, categoria__nome__iexact='Ração')
                            except Produto.DoesNotExist:
                                racao_nao_encontrada_msgs.append(f"Linha {index + 2}: Ração '{racao_nome}' não encontrada ou não pertence à categoria 'Ração'.")
                            except Produto.MultipleObjectsReturned:
                                racao_nao_encontrada_msgs.append(f"Linha {index + 2}: Múltiplas rações encontradas para '{racao_nome}'.")
                        
                        # Converte a hora para o formato time do Python
                        hora_inicio = None
                        hora_str = str(row.get('hora_inicio', ''))
                        if hora_str:
                            try:
                                if ':' in hora_str: # Formato HH:MM ou HH:MM:SS
                                    parts = list(map(int, hora_str.split(':')))
                                    if len(parts) == 2: hora_inicio = time(parts[0], parts[1])
                                    elif len(parts) == 3: hora_inicio = time(parts[0], parts[1], parts[2])
                                else: # Tenta converter de float (ex: 0.2916666666666667 para 07:00)
                                    total_seconds = float(hora_str) * 24 * 3600
                                    h = int(total_seconds // 3600)
                                    m = int((total_seconds % 3600) // 60)
                                    hora_inicio = time(h, m)
                            except (ValueError, TypeError):
                                pass # hora_inicio permanece None

                        CurvaCrescimentoDetalhe.objects.create(
                            curva=curva,
                            periodo_semana=row['periodo_semana'],
                            periodo_dias=row['periodo_dias'],
                            peso_inicial=row['peso_inicial'],
                            peso_final=row['peso_final'],
                            ganho_de_peso=row['ganho_de_peso'],
                            numero_tratos=row['numero_tratos'],
                            hora_inicio=hora_inicio,
                            arracoamento_biomassa_perc=row['arracoamento_biomassa_perc'],
                            mortalidade_presumida_perc=row['mortalidade_presumida_perc'],
                            racao=racao_obj, # Salva o objeto Produto ou None
                            gpd=row['gpd'],
                            tca=row['tca'],
                        )
                
                if racao_nao_encontrada_msgs:
                    messages.warning(request, "Curva importada com avisos: " + "; ".join(racao_nao_encontrada_msgs))
                else:
                    messages.success(request, "Curva de crescimento importada com sucesso!")
                
                # Retorna JSON para requisições AJAX
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'sucesso': True,
                        'mensagem': messages.get_messages(request)._loaded_messages[-1].message, # Pega a última mensagem
                        'redirect_url': reverse('producao:lista_curvas')
                    })
                return redirect('producao:lista_curvas')

            except Exception as e:
                error_message = f"Ocorreu um erro ao processar o arquivo: {e}"
                if "KeyError" in str(e):
                    error_message = "Verifique se todas as colunas obrigatórias estão presentes no arquivo Excel e com os nomes corretos."
                messages.error(request, error_message)
                
                # Retorna JSON para requisições AJAX em caso de erro
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'sucesso': False,
                        'mensagem': error_message,
                        'erros': form.errors # Se houver erros de formulário
                    }, status=400)
                
                context = {'form': form, 'error_message': error_message}
                return render_ajax_or_base(request, 'producao/curvas/importar_curva.html', context)
    else:
        form = ImportarCurvaForm()
    
    return render_ajax_or_base(request, 'producao/curvas/importar_curva.html', {'form': form})

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


# === API para Edição Interativa de Detalhes da Curva ===

from produto.models import Produto, CategoriaProduto # Importa Produto e CategoriaProduto

class AtualizarDetalheCurvaAPIView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'producao.change_curvacrescimentodetalhe'
    raise_exception = True

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            detalhe_id = data.get('detalhe_id')
            racao_id = data.get('racao_id')
            fill_down = data.get('fill_down', False)

            if not detalhe_id:
                return JsonResponse({'sucesso': False, 'mensagem': 'ID do detalhe da curva não fornecido.'}, status=400)

            try:
                detalhe = CurvaCrescimentoDetalhe.objects.get(pk=detalhe_id)
            except CurvaCrescimentoDetalhe.DoesNotExist:
                return JsonResponse({'sucesso': False, 'mensagem': 'Detalhe da curva não encontrado.'}, status=404)

            racao_obj = None
            if racao_id:
                try:
                    racao_obj = Produto.objects.get(pk=racao_id)
                    # Opcional: Verificar se a categoria do produto é 'Ração'
                    if racao_obj.categoria and racao_obj.categoria.nome.lower() != 'ração':
                        return JsonResponse({'sucesso': False, 'mensagem': 'Produto selecionado não é uma ração.'}, status=400)
                except Produto.DoesNotExist:
                    return JsonResponse({'sucesso': False, 'mensagem': 'Ração selecionada não encontrada.'}, status=404)
            
            with transaction.atomic():
                detalhe.racao = racao_obj
                detalhe.save()

                if fill_down:
                    # Atualiza todas as linhas subsequentes da mesma curva
                    CurvaCrescimentoDetalhe.objects.filter(
                        curva=detalhe.curva,
                        periodo_semana__gt=detalhe.periodo_semana
                    ).update(racao=racao_obj)
            
            return JsonResponse({'sucesso': True, 'mensagem': 'Detalhe da curva atualizado com sucesso.'}) 

        except json.JSONDecodeError:
            return JsonResponse({'sucesso': False, 'mensagem': 'Requisição JSON inválida.'}, status=400)
        except Exception as e:
            return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao atualizar detalhe da curva: {str(e)}'}, status=500)

