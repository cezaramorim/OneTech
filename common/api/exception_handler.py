from rest_framework.views import exception_handler

from common.security_audit import log_permission_denied


NOT_AUTH_CODES = {'not_authenticated', 'authentication_failed'}
PERMISSION_DENIED_CODE = 'permission_denied'


def _extract_detail_and_code(data):
    if isinstance(data, dict):
        detail = data.get('detail')
    else:
        detail = data
    code = getattr(detail, 'code', None)
    return detail, code


def onetech_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    detail, detail_code = _extract_detail_and_code(response.data)

    if detail_code in NOT_AUTH_CODES or response.status_code == 401:
        response.status_code = 401
        response.data = {
            'success': False,
            'message': str(detail) if detail else 'Autenticacao obrigatoria.',
            'code': 'not_authenticated',
            'detail': detail,
        }
        return response

    if detail_code == PERMISSION_DENIED_CODE or response.status_code == 403:
        request = (context or {}).get('request')
        if request is not None:
            log_permission_denied(request, code='permission_denied', detail=str(detail or ''))
        response.data = {
            'success': False,
            'message': 'Permissao negada para executar esta acao.',
            'code': 'permission_denied',
            'detail': detail,
        }

    return response