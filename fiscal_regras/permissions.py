from django.core.exceptions import PermissionDenied


def ensure_override_permission(user):
    if not user.has_perm('fiscal_regras.override_aliquota_item'):
        raise PermissionDenied
