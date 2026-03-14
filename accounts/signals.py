from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from common.security_audit import log_system_event


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    if request is None or user is None:
        return

    log_system_event(
        request,
        code='auth_login_success',
        detail=f'Login bem-sucedido para user_id={getattr(user, "id", "")}',
        metadata={
            'username': getattr(user, 'username', ''),
            'user_id': getattr(user, 'id', None),
        },
    )


@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    if request is None:
        return

    log_system_event(
        request,
        code='auth_logout',
        detail=f'Logout executado para user_id={getattr(user, "id", "")}',
        metadata={
            'username': getattr(user, 'username', ''),
            'user_id': getattr(user, 'id', None),
        },
    )


@receiver(user_login_failed)
def on_user_login_failed(sender, credentials, request, **kwargs):
    if request is None:
        return

    username = ''
    if isinstance(credentials, dict):
        username = str(credentials.get('username') or credentials.get('email') or '')

    log_system_event(
        request,
        code='auth_login_failed',
        detail=f'Falha de login para identificador={username}',
        metadata={
            'username': username,
            'credentials_keys': sorted(list(credentials.keys())) if isinstance(credentials, dict) else [],
        },
    )