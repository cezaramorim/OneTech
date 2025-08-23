# utils/decorators.py
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.views import redirect_to_login
from functools import wraps

def login_required_json(viewfunc):
    @wraps(viewfunc)
    def _wrapped(request, *args, **kwargs):
        if request.user.is_authenticated:
            return viewfunc(request, *args, **kwargs)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            next_url = request.get_full_path()
            login_url = f"{settings.LOGIN_URL}?next={next_url}"
            return JsonResponse({"success": False, "redirect_url": login_url}, status=401)
        return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
    return _wrapped
