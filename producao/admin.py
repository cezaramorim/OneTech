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
    # Novos modelos de arraçoamento
    LoteDiario,
    ArracoamentoSugerido,
    ArracoamentoRealizado
)

admin.site.register(LinhaProducao)
admin.site.register(StatusTanque)
admin.site.register(FaseProducao)
admin.site.register(TipoTanque)
admin.site.register(Atividade)
admin.site.register(CurvaCrescimento)
@admin.register(Tanque)
class TanqueAdmin(admin.ModelAdmin):
    list_display = (
        "id","nome","data_criacao","largura","profundidade","comprimento",
        "metro_cubico","metro_quadrado","ha",
        "unidade","fase","tipo_tanque","linha_producao","sequencia",
        "malha","status_tanque","tag_tanque",
    )
admin.site.register(Lote)
admin.site.register(EventoManejo)


# Registro dos novos modelos
admin.site.register(LoteDiario)
admin.site.register(ArracoamentoSugerido)
admin.site.register(ArracoamentoRealizado)