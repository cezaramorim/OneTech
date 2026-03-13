# utils/decorators.py
from functools import wraps

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse

from common.security_audit import log_permission_denied


def _is_json_request(request):
    xrw = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    accepts_json = 'application/json' in (request.headers.get('Accept') or '')
    content_json = 'application/json' in (request.content_type or '')
    return xrw or accepts_json or content_json


def login_required_json(viewfunc):
    @wraps(viewfunc)
    def _wrapped(request, *args, **kwargs):
        if request.user.is_authenticated:
            return viewfunc(request, *args, **kwargs)
        if _is_json_request(request):
            next_url = request.get_full_path()
            login_url = f"{settings.LOGIN_URL}?next={next_url}"
            return JsonResponse({"success": False, "redirect_url": login_url}, status=401)
        return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)

    return _wrapped


def permission_required_json(perm, raise_exception=True):
    required_perms = (perm,) if isinstance(perm, str) else tuple(perm)

    def decorator(viewfunc):
        @wraps(viewfunc)
        def _wrapped(request, *args, **kwargs):
            if request.user.has_perms(required_perms):
                return viewfunc(request, *args, **kwargs)

            log_permission_denied(request, code='permission_denied', detail=','.join(required_perms))

            if _is_json_request(request):
                return JsonResponse(
                    {
                        'success': False,
                        'message': 'Permissao negada para executar esta acao.',
                        'code': 'permission_denied',
                    },
                    status=403,
                )

            if raise_exception:
                raise PermissionDenied

            return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)

        return _wrapped

    return decorator