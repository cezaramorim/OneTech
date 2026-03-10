import re

from django.core.exceptions import ValidationError


NCM_PREFIX_RE = re.compile(r'^\d{2,8}$')


def validate_ncm_prefixo(value):
    valor = re.sub(r'\D', '', str(value or ''))
    if not NCM_PREFIX_RE.match(valor):
        raise ValidationError('NCM prefixo deve conter somente numeros e ter entre 2 e 8 digitos.')
