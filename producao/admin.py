from django.contrib import admin
from .models import (
    LinhaProducao,
    StatusTanque,
    FaseProducao,
    TipoTanque,
    Atividade,
    CurvaCrescimento,
    Tanque,
    Lote,
    EventoManejo,
    AlimentacaoDiaria
)

admin.site.register(LinhaProducao)
admin.site.register(StatusTanque)
admin.site.register(FaseProducao)
admin.site.register(TipoTanque)
admin.site.register(Atividade)
admin.site.register(CurvaCrescimento)
admin.site.register(Tanque)
admin.site.register(Lote)
admin.site.register(EventoManejo)
admin.site.register(AlimentacaoDiaria)