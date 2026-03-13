import logging

from django.utils.timezone import now

logger = logging.getLogger('security.authz')


def _extract_ip_address(request):
    xff = (request.META.get('HTTP_X_FORWARDED_FOR') or '').strip()
    if xff:
        return xff.split(',')[0].strip()
    return (request.META.get('REMOTE_ADDR') or '').strip()


def _persist_security_event(request, event_type, code='', detail='', metadata=None):
    try:
        from control.models import SecurityAuditEvent

        user = getattr(request, 'user', None)
        tenant = getattr(request, 'tenant', None)

        SecurityAuditEvent.objects.create(
            event_type=event_type,
            code=code or '',
            detail=detail or '',
            method=getattr(request, 'method', ''),
            path=getattr(request, 'path', ''),
            host=(request.get_host() if hasattr(request, 'get_host') else ''),
            ip_address=_extract_ip_address(request),
            tenant_slug=(getattr(tenant, 'slug', '') or ''),
            user=(user if getattr(user, 'is_authenticated', False) else None),
            metadata=(metadata or {}),
        )
    except Exception:
        # Nunca interromper a resposta por falha de auditoria.
        pass


def log_system_event(request, code='system_event', detail='', metadata=None):
    _persist_security_event(
        request,
        event_type='SYSTEM',
        code=code,
        detail=detail,
        metadata=(metadata or {'timestamp': now().isoformat()}),
    )


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

    _persist_security_event(
        request,
        event_type='AUTHZ_DENIED',
        code=code,
        detail=detail,
    )
