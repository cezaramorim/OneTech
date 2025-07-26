from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import resolve_url

class AjaxLoginRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Verifica se a requisição é AJAX, a resposta é um redirecionamento,
        # e o usuário não está autenticado.
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        
        if is_ajax and response.status_code == 302 and not request.user.is_authenticated:
            # Pega a URL de destino do redirecionamento
            redirect_url = response.url
            
            # Compara com a URL de login resolvida
            login_url = resolve_url(settings.LOGIN_URL)

            # Se o destino for a página de login, retorna 401
            if login_url in redirect_url:
                return JsonResponse({'redirect_url': redirect_url}, status=401)

        return response