from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect, resolve_url


class AjaxLoginRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        login_url = resolve_url(settings.LOGIN_URL)

        if is_ajax and response.status_code == 302 and not request.user.is_authenticated:
            redirect_url = getattr(response, 'url', '')
            if login_url in redirect_url:
                return JsonResponse({'redirect_url': redirect_url}, status=401)

        if response.status_code == 403 and not request.user.is_authenticated:
            redirect_url = f'{login_url}?next={request.get_full_path()}'
            if is_ajax:
                return JsonResponse({'redirect_url': redirect_url}, status=401)
            return redirect(redirect_url)

        return response
