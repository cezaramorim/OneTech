from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q
from .models import Tanque, CurvaCrescimento, Lote, EventoManejo, AlimentacaoDiaria # Importa AlimentacaoDiaria
from .forms import TanqueForm, CurvaCrescimentoForm, LoteForm, EventoManejoForm, AlimentacaoDiariaForm # Importa AlimentacaoDiariaForm
import json

def render_ajax_or_base(request, partial_template, context=None):
    context = context or {}
    return render(request, 'base.html', {'content_template': partial_template, **context})

@login_required
@permission_required('producao.view_tanque', raise_exception=True)
def lista_tanques_view(request):
    tanques = Tanque.objects.all()

    termo = request.GET.get('termo_tanque', '').strip()
    if termo:
        tanques = tanques.filter(
            Q(nome__icontains=termo) |
            Q(linha_producao__nome__icontains=termo) |
            Q(tipo_tanque__nome__icontains=termo) |
            Q(atividade__nome__icontains=termo) |
            Q(status_tanque__nome__icontains=termo)
        )

    return render_ajax_or_base(request, 'producao/tanques/lista_tanques.html', {
        'tanques': tanques,
        'termo_busca': termo,
    })

@login_required
@permission_required('producao.add_tanque', raise_exception=True)
def cadastrar_tanque_view(request):
    form = TanqueForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Tanque cadastrado com sucesso!")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': True, 'redirect_url': '/producao/tanques/'}) # Redireciona para a lista
            return redirect('producao:lista_tanques')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': False, 'erros': form.errors}, status=400)
    
    return render_ajax_or_base(request, 'producao/tanques/cadastrar_tanque.html', {'form': form})

@login_required
@permission_required('producao.change_tanque', raise_exception=True)
def editar_tanque_view(request, pk):
    tanque = get_object_or_404(Tanque, pk=pk)
    form = TanqueForm(request.POST or None, instance=tanque)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Tanque atualizado com sucesso!")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': True, 'redirect_url': '/producao/tanques/'}) # Redireciona para a lista
            return redirect('producao:lista_tanques')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': False, 'erros': form.errors}, status=400)
    
    return render_ajax_or_base(request, 'producao/tanques/editar_tanque.html', {'form': form, 'tanque': tanque})

@login_required
@permission_required('producao.delete_tanque', raise_exception=True)
def excluir_tanques_multiplos_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            tanque_ids = data.get('ids', [])
            if not tanque_ids:
                return JsonResponse({'sucesso': False, 'mensagem': 'Nenhum tanque selecionado para exclusão.'}, status=400)
            
            Tanque.objects.filter(pk__in=tanque_ids).delete()
            messages.success(request, f"{len(tanque_ids)} tanque(s) excluído(s) com sucesso!")
            return JsonResponse({'sucesso': True, 'redirect_url': '/producao/tanques/'})
        except json.JSONDecodeError:
            return JsonResponse({'sucesso': False, 'mensagem': 'Requisição inválida.'}, status=400)
        except Exception as e:
            return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao excluir tanques: {str(e)}'}, status=500)
    return JsonResponse({'sucesso': False, 'mensagem': 'Método não permitido.'}, status=405)

@login_required
@permission_required('producao.view_curvacrescimento', raise_exception=True)
def lista_curvas_view(request):
    curvas = CurvaCrescimento.objects.all()

    termo = request.GET.get('termo_curva', '').strip()
    if termo:
        curvas = curvas.filter(
            Q(nome__icontains=termo) |
            Q(produto_racao__nome__icontains=termo)
        )

    return render_ajax_or_base(request, 'producao/curvas/lista_curvas.html', {
        'curvas': curvas,
        'termo_busca': termo,
    })

@login_required
@permission_required('producao.add_curvacrescimento', raise_exception=True)
def cadastrar_curva_view(request):
    form = CurvaCrescimentoForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Curva de Crescimento cadastrada com sucesso!")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': True, 'redirect_url': '/producao/curvas/'})
            return redirect('producao:lista_curvas')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': False, 'erros': form.errors}, status=400)
    
    return render_ajax_or_base(request, 'producao/curvas/cadastrar_curva.html', {'form': form})

@login_required
@permission_required('producao.change_curvacrescimento', raise_exception=True)
def editar_curva_view(request, pk):
    curva = get_object_or_404(CurvaCrescimento, pk=pk)
    form = CurvaCrescimentoForm(request.POST or None, instance=curva)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Curva de Crescimento atualizada com sucesso!")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': True, 'redirect_url': '/producao/curvas/'})
            return redirect('producao:lista_curvas')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': False, 'erros': form.errors}, status=400)
    
    return render_ajax_or_base(request, 'producao/curvas/editar_curva.html', {'form': form, 'curva': curva})

@login_required
@permission_required('producao.delete_curvacrescimento', raise_exception=True)
def excluir_curvas_multiplas_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            curva_ids = data.get('ids', [])
            if not curva_ids:
                return JsonResponse({'sucesso': False, 'mensagem': 'Nenhuma curva selecionada para exclusão.'}, status=400)
            
            CurvaCrescimento.objects.filter(pk__in=curva_ids).delete()
            messages.success(request, f"{len(curva_ids)} curva(s) excluída(s) com sucesso!")
            return JsonResponse({'sucesso': True, 'redirect_url': '/producao/curvas/'})
        except json.JSONDecodeError:
            return JsonResponse({'sucesso': False, 'mensagem': 'Requisição inválida.'}, status=400)
        except Exception as e:
            return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao excluir curvas: {str(e)}'}, status=500)
    return JsonResponse({'sucesso': False, 'mensagem': 'Método não permitido.'}, status=405)

@login_required
@permission_required('producao.view_lote', raise_exception=True)
def lista_lotes_view(request):
    lotes = Lote.objects.all()

    termo = request.GET.get('termo_lote', '').strip()
    if termo:
        lotes = lotes.filter(
            Q(nome__icontains=termo) |
            Q(curva_crescimento__nome__icontains=termo) |
            Q(fase_producao__nome__icontains=termo) |
            Q(tanque_atual__nome__icontains=termo)
        )

    return render_ajax_or_base(request, 'producao/lotes/lista_lotes.html', {
        'lotes': lotes,
        'termo_busca': termo,
    })

@login_required
@permission_required('producao.add_lote', raise_exception=True)
def cadastrar_lote_view(request):
    form = LoteForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Lote cadastrado com sucesso!")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': True, 'redirect_url': '/producao/lotes/'})
            return redirect('producao:lista_lotes')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': False, 'erros': form.errors}, status=400)
    
    return render_ajax_or_base(request, 'producao/lotes/cadastrar_lote.html', {'form': form})

@login_required
@permission_required('producao.change_lote', raise_exception=True)
def editar_lote_view(request, pk):
    lote = get_object_or_404(Lote, pk=pk)
    form = LoteForm(request.POST or None, instance=lote)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Lote atualizado com sucesso!")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': True, 'redirect_url': '/producao/lotes/'})
            return redirect('producao:lista_lotes')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': False, 'erros': form.errors}, status=400)
    
    return render_ajax_or_base(request, 'producao/lotes/editar_lote.html', {'form': form, 'lote': lote})

@login_required
@permission_required('producao.delete_lote', raise_exception=True)
def excluir_lotes_multiplos_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lote_ids = data.get('ids', [])
            if not lote_ids:
                return JsonResponse({'sucesso': False, 'mensagem': 'Nenhum lote selecionado para exclusão.'}, status=400)
            
            Lote.objects.filter(pk__in=lote_ids).delete()
            messages.success(request, f"{len(lote_ids)} lote(s) excluído(s) com sucesso!")
            return JsonResponse({'sucesso': True, 'redirect_url': '/producao/lotes/'})
        except json.JSONDecodeError:
            return JsonResponse({'sucesso': False, 'mensagem': 'Requisição inválida.'}, status=400)
        except Exception as e:
            return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao excluir lotes: {str(e)}'}, status=500)
    return JsonResponse({'sucesso': False, 'mensagem': 'Método não permitido.'}, status=405)

@login_required
@permission_required('producao.view_eventomanejo', raise_exception=True)
def lista_eventos_view(request):
    eventos = EventoManejo.objects.all()

    termo = request.GET.get('termo_evento', '').strip()
    if termo:
        eventos = eventos.filter(
            Q(tipo_evento__icontains=termo) |
            Q(lote__nome__icontains=termo) |
            Q(tanque_origem__nome__icontains=termo) |
            Q(tanque_destino__nome__icontains=termo)
        )

    return render_ajax_or_base(request, 'producao/eventos/lista_eventos.html', {
        'eventos': eventos,
        'termo_busca': termo,
    })

@login_required
@permission_required('producao.add_eventomanejo', raise_exception=True)
def registrar_evento_view(request):
    form = EventoManejoForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            evento = form.save(commit=False)
            # Lógica para atualizar Lote e Tanque (quantidade, peso, biomassa, tanque atual)
            # Isso será implementado em uma etapa posterior, após a criação dos modelos de Lote e Tanque
            evento.save()
            messages.success(request, "Evento de Manejo registrado com sucesso!")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': True, 'redirect_url': '/producao/eventos/'})
            return redirect('producao:lista_eventos')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': False, 'erros': form.errors}, status=400)
    
    return render_ajax_or_base(request, 'producao/eventos/registrar_evento.html', {'form': form})

@login_required
@permission_required('producao.change_eventomanejo', raise_exception=True)
def editar_evento_view(request, pk):
    evento = get_object_or_404(EventoManejo, pk=pk)
    form = EventoManejoForm(request.POST or None, instance=evento)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Evento de Manejo atualizado com sucesso!")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': True, 'redirect_url': '/producao/eventos/'})
            return redirect('producao:lista_eventos')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': False, 'erros': form.errors}, status=400)
    
    return render_ajax_or_base(request, 'producao/eventos/editar_evento.html', {'form': form, 'evento': evento})

@login_required
@permission_required('producao.delete_eventomanejo', raise_exception=True)
def excluir_eventos_multiplos_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            evento_ids = data.get('ids', [])
            if not evento_ids:
                return JsonResponse({'sucesso': False, 'mensagem': 'Nenhum evento selecionado para exclusão.'}, status=400)
            
            EventoManejo.objects.filter(pk__in=evento_ids).delete()
            messages.success(request, f"{len(evento_ids)} evento(s) excluído(s) com sucesso!")
            return JsonResponse({'sucesso': True, 'redirect_url': '/producao/eventos/'})
        except json.JSONDecodeError:
            return JsonResponse({'sucesso': False, 'mensagem': 'Requisição inválida.'}, status=400)
        except Exception as e:
            return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao excluir eventos: {str(e)}'}, status=500)
    return JsonResponse({'sucesso': False, 'mensagem': 'Método não permitido.'}, status=405)

@login_required
@permission_required('producao.view_alimentacaodiaria', raise_exception=True)
def lista_alimentacao_view(request):
    alimentacoes = AlimentacaoDiaria.objects.all()

    termo = request.GET.get('termo_alimentacao', '').strip()
    if termo:
        alimentacoes = alimentacoes.filter(
            Q(lote__nome__icontains=termo) |
            Q(produto_racao__nome__icontains=termo)
        )

    return render_ajax_or_base(request, 'producao/alimentacao/lista_alimentacao.html', {
        'alimentacoes': alimentacoes,
        'termo_busca': termo,
    })

@login_required
@permission_required('producao.add_alimentacaodiaria', raise_exception=True)
def registrar_alimentacao_view(request):
    form = AlimentacaoDiariaForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Alimentação Diária registrada com sucesso!")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': True, 'redirect_url': '/producao/alimentacao/'})
            return redirect('producao:lista_alimentacao')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': False, 'erros': form.errors}, status=400)
    
    return render_ajax_or_base(request, 'producao/alimentacao/registrar_alimentacao.html', {'form': form})

@login_required
@permission_required('producao.change_alimentacaodiaria', raise_exception=True)
def editar_alimentacao_view(request, pk):
    alimentacao = get_object_or_404(AlimentacaoDiaria, pk=pk)
    form = AlimentacaoDiariaForm(request.POST or None, instance=alimentacao)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Alimentação Diária atualizada com sucesso!")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': True, 'redirect_url': '/producao/alimentacao/'})
            return redirect('producao:lista_alimentacao')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'sucesso': False, 'erros': form.errors}, status=400)
    
    return render_ajax_or_base(request, 'producao/alimentacao/editar_alimentacao.html', {'form': form, 'alimentacao': alimentacao})

@login_required
@permission_required('producao.delete_alimentacaodiaria', raise_exception=True)
def excluir_alimentacao_multipla_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            alimentacao_ids = data.get('ids', [])
            if not alimentacao_ids:
                return JsonResponse({'sucesso': False, 'mensagem': 'Nenhuma alimentação selecionada para exclusão.'}, status=400)
            
            AlimentacaoDiaria.objects.filter(pk__in=alimentacao_ids).delete()
            messages.success(request, f"{len(alimentacao_ids)} alimentação(ões) excluída(s) com sucesso!")
            return JsonResponse({'sucesso': True, 'redirect_url': '/producao/alimentacao/'})
        except json.JSONDecodeError:
            return JsonResponse({'sucesso': False, 'mensagem': 'Requisição inválida.'}, status=400)
        except Exception as e:
            return JsonResponse({'sucesso': False, 'mensagem': f'Erro ao excluir alimentações: {str(e)}'}, status=500)
    return JsonResponse({'sucesso': False, 'mensagem': 'Método não permitido.'}, status=405)