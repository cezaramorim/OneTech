from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib import messages
from common.messages_utils import get_app_messages
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
import json


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

            # Recupera os nomes dos objetos antes de excluí-los
            objects_to_delete = self.model.objects.filter(pk__in=ids)
            deleted_names = [str(obj) for obj in objects_to_delete] # Converte para string para pegar o __str__ do modelo

            deleted_count, _ = objects_to_delete.delete()

            if deleted_count > 0:
                if len(deleted_names) == 1:
                    message_detail = f"'{deleted_names[0]}'"
                else:
                    message_detail = f"'{', '.join(deleted_names)}'"
                message = app_messages.success_deleted(self.model._meta.verbose_name_plural, message_detail)
            else:
                message = app_messages.error('Nenhum item foi excluído.') # Caso não encontre nenhum para excluir
            
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
