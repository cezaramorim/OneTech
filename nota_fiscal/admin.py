from django.contrib import admin

from .models import NotaFiscal, ItemNotaFiscal, DuplicataNotaFiscal, TransporteNotaFiscal


@admin.register(TransporteNotaFiscal)
class TransporteNotaFiscalAdmin(admin.ModelAdmin):
    list_display = ('nota_fiscal', 'transportadora_nome', 'transportadora_cnpj', 'modalidade_frete')
    search_fields = ('nota_fiscal__numero', 'transportadora_nome', 'transportadora_cnpj')


admin.site.register(NotaFiscal)
admin.site.register(ItemNotaFiscal)
admin.site.register(DuplicataNotaFiscal)
