import logging


logger = logging.getLogger('security.authz')


def log_permission_denied(request, code='permission_denied', detail=''):
    user = getattr(request, 'user', None)
    tenant = getattr(request, 'tenant', None)

    user_id = getattr(user, 'id', None)
    username = getattr(user, 'username', None)
    is_authenticated = bool(getattr(user, 'is_authenticated', False))

    tenant_id = getattr(tenant, 'id', None)
    tenant_slug = getattr(tenant, 'slug', None)

    method = getattr(request, 'method', '')
    path = getattr(request, 'path', '')

    try:
        host = request.get_host()
    except Exception:
        host = ''

    logger.warning(
        'AUTHZ_DENIED code=%s user_id=%s username=%s is_authenticated=%s method=%s path=%s host=%s tenant_id=%s tenant_slug=%s detail=%s',
        code,
        user_id,
        username,
        is_authenticated,
        method,
        path,
        host,
        tenant_id,
        tenant_slug,
        detail,
    )