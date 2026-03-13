import logging

from django.contrib.auth import get_user_model
from django.db import DatabaseError, IntegrityError
from django.utils.timezone import now

logger = logging.getLogger('security.authz')


def _extract_ip_address(request):
    xff = (request.META.get('HTTP_X_FORWARDED_FOR') or '').strip()
    if xff:
        return xff.split(',')[0].strip()
    return (request.META.get('REMOTE_ADDR') or '').strip()


def _resolve_default_user_id(user_obj):
    if not getattr(user_obj, 'is_authenticated', False):
        return None

    user_id = getattr(user_obj, 'id', None)
    if not user_id:
        return None

    user_model = get_user_model()
    exists_on_default = user_model.objects.using('default').filter(pk=user_id).exists()
    return user_id if exists_on_default else None


def _persist_security_event(request, event_type, code='', detail='', metadata=None):
    from control.models import SecurityAuditEvent

    user = getattr(request, 'user', None)
    tenant = getattr(request, 'tenant', None)

    metadata_payload = dict(metadata or {})
    if getattr(user, 'is_authenticated', False):
        metadata_payload.setdefault('request_user_id', getattr(user, 'id', None))
        metadata_payload.setdefault('request_username', getattr(user, 'username', ''))
        metadata_payload.setdefault('request_user_db', getattr(getattr(user, '_state', None), 'db', ''))

    metadata_payload.setdefault('request_tenant_slug', getattr(tenant, 'slug', '') or '')

    payload = {
        'event_type': event_type,
        'code': code or '',
        'detail': detail or '',
        'method': getattr(request, 'method', ''),
        'path': getattr(request, 'path', ''),
        'host': (request.get_host() if hasattr(request, 'get_host') else ''),
        'ip_address': _extract_ip_address(request),
        'tenant_slug': (getattr(tenant, 'slug', '') or ''),
        'metadata': metadata_payload,
        # Evita bloqueio de relacao por router usando user_id direto no banco default.
        'user_id': _resolve_default_user_id(user),
    }

    try:
        SecurityAuditEvent.objects.create(**payload)
        return
    except (ValueError, DatabaseError, IntegrityError):
        # Fallback: preserva telemetria mesmo que a referencia de usuario nao seja viavel.
        payload['user_id'] = None
        payload['metadata']['audit_fallback'] = 'user_omitted'
        try:
            SecurityAuditEvent.objects.create(**payload)
            return
        except Exception:
            logger.exception(
                'Falha ao persistir evento de seguranca (fallback tambem falhou). '
                'event_type=%s code=%s path=%s',
                event_type,
                code,
                payload.get('path', ''),
            )
            return
    except Exception:
        logger.exception(
            'Falha ao persistir evento de seguranca. event_type=%s code=%s path=%s',
            event_type,
            code,
            payload.get('path', ''),
        )
        return


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