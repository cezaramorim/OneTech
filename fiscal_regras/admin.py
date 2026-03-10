from django.contrib import admin

from .models import RegraAliquotaICMS


@admin.register(RegraAliquotaICMS)
class RegraAliquotaICMSAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'ativo', 'descricao', 'ncm_prefixo', 'tipo_operacao', 'modalidade',
        'uf_origem', 'uf_destino', 'aliquota_icms', 'prioridade', 'vigencia_inicio', 'vigencia_fim',
    )
    list_filter = ('ativo', 'tipo_operacao', 'modalidade', 'uf_origem', 'uf_destino')
    search_fields = ('descricao', 'ncm_prefixo', 'uf_origem', 'uf_destino', 'observacoes')
