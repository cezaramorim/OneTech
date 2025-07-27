from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib import messages
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
import json

def render_ajax_or_base(request, partial_template, context=None):
    """
    Renderiza um template parcial dentro do base.html para requisições normais
    ou apenas o template parcial para requisições AJAX.
    """
    context = context or {}
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, partial_template, context)
    return render(request, 'base.html', {'content_template': partial_template, **context})


class AjaxFormMixin:
    """
    Mixin para CreateView e UpdateView que lida com submissões de formulário
    via AJAX, retornando JSON, ou redirecionando em requisições normais.
    """
    success_url = None
    success_message = ""

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, self.success_message)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'sucesso': True,
                'redirect_url': str(self.get_success_url())
            })
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'sucesso': False, 'erros': form.errors}, status=400)
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
        try:
            data = json.loads(request.body)
            ids = data.get('ids', [])
            if not ids:
                return JsonResponse({'sucesso': False, 'mensagem': 'Nenhum item selecionado para exclusão.'}, status=400)

            self.model.objects.filter(pk__in=ids).delete()
            
            success_message = f"{len(ids)} registro(s) excluído(s) com sucesso!"
            messages.success(request, success_message)
            
            return JsonResponse({
                'sucesso': True, 
                'mensagem': success_message,
                'redirect_url': str(reverse_lazy(self.success_url_name))
            })
        except json.JSONDecodeError:
            return JsonResponse({'sucesso': False, 'mensagem': 'Requisição JSON inválida.'}, status=400)
        except Exception as e:
            return JsonResponse({'sucesso': False, 'mensagem': f'Ocorreu um erro inesperado: {e}'}, status=500)
