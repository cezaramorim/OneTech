from django.contrib import admin
from .models import Cfop, NaturezaOperacao

@admin.register(Cfop)
class CfopAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descricao')
    search_fields = ('codigo', 'descricao')

@admin.register(NaturezaOperacao)
class NaturezaOperacaoAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'codigo')
    search_fields = ('descricao', 'codigo')
    list_filter = ('codigo',)