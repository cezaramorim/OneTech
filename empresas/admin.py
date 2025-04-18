from django.contrib import admin
from .models import EmpresaAvancada

@admin.register(EmpresaAvancada)
class EmpresaAvancadaAdmin(admin.ModelAdmin):
    list_display = ('tipo_empresa', 'razao_social', 'nome', 'cpf', 'cnpj', 'email', 'cidade', 'vendedor')
    list_filter = ('tipo_empresa', 'uf', 'cidade')
    search_fields = ('razao_social', 'nome_fantasia', 'nome', 'cpf', 'cnpj', 'email')
    readonly_fields = ('data_cadastro',)
    ordering = ('-data_cadastro',)