from django.contrib import admin

from .models import SecurityAuditEvent, Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug', 'dominio', 'ativo', 'data_criacao')
    list_filter = ('ativo',)
    search_fields = ('nome', 'dominio', 'razao_social', 'cnpj')
    ordering = ('-data_criacao',)

    fieldsets = (
        ('Informacoes Gerais', {
            'fields': ('nome', 'slug', 'dominio', 'ativo')
        }),
        ('Dados da Empresa (NF-e e Branding)', {
            'fields': ('razao_social', 'nome_fantasia', 'cnpj', 'ie', 'logo')
        }),
        ('Credenciais do Banco de Dados', {
            'classes': ('collapse',),
            'fields': ('db_name', 'db_user', 'db_password', 'db_host', 'db_port')
        }),
        ('Configuracoes Fiscais (NF-e)', {
            'classes': ('collapse',),
            'fields': ('certificado_a1', 'senha_certificado', 'csc', 'id_token')
        }),
    )


@admin.register(SecurityAuditEvent)
class SecurityAuditEventAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'event_type', 'code', 'path', 'method', 'user', 'tenant_slug', 'ip_address')
    list_filter = ('event_type', 'code', 'created_at')
    search_fields = ('path', 'detail', 'host', 'tenant_slug', 'user__username')
    ordering = ('-created_at',)
