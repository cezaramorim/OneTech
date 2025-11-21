from django.contrib import admin
from .models import Tenant

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug', 'dominio', 'ativo', 'data_criacao')
    list_filter = ('ativo',)
    search_fields = ('nome', 'dominio', 'razao_social', 'cnpj')
    ordering = ('-data_criacao',)
    
    fieldsets = (
        ('Informações Gerais', {
            'fields': ('nome', 'slug', 'dominio', 'ativo')
        }),
        ('Dados da Empresa (NF-e e Branding)', {
            'fields': ('razao_social', 'nome_fantasia', 'cnpj', 'ie', 'logo')
        }),
        ('Credenciais do Banco de Dados', {
            'classes': ('collapse',),
            'fields': ('db_name', 'db_user', 'db_password', 'db_host', 'db_port')
        }),
        ('Configurações Fiscais (NF-e)', {
            'classes': ('collapse',),
            'fields': ('certificado_a1', 'senha_certificado', 'csc', 'id_token')
        }),
    )