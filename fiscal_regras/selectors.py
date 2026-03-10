from django.db.models import Q

from .models import RegraAliquotaICMS


def regras_icms_vigentes(data_referencia):
    return RegraAliquotaICMS.objects.filter(
        ativo=True,
        vigencia_inicio__lte=data_referencia,
    ).filter(
        Q(vigencia_fim__isnull=True) | Q(vigencia_fim__gte=data_referencia)
    )
