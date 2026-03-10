from django.contrib import admin

from .models import CondicaoPagamento


@admin.register(CondicaoPagamento)
class CondicaoPagamentoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descricao', 'quantidade_parcelas', 'updated_at')
    search_fields = ('codigo', 'descricao', 'observacoes')
    ordering = ('codigo',)
