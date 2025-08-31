from django.http import JsonResponse
from django.contrib import messages

class ClearAjaxMessagesMiddleware:
    """
    Em qualquer requisição AJAX que retorne JsonResponse,
    consome (drena) as mensagens do Django para não reaparecerem no reload.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Detecta AJAX clássico
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if is_ajax and isinstance(response, JsonResponse):
            # Consumir mensagens: iterar já marca como usadas
            list(messages.get_messages(request))
        return response