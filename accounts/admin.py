from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User

    # Adiciona explicitamente o campo personalizado 'nome_completo' e o campo personalizado 'grupos'
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Extras', {'fields': ('nome_completo', 'grupos')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informações Extras', {'fields': ('nome_completo', 'grupos')}),
    )

admin.site.register(User, CustomUserAdmin)

# Garanta que Group esteja visível no admin
admin.site.unregister(Group)
admin.site.register(Group)
