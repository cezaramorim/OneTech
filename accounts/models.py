from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class User(AbstractUser):
    nome_completo = models.CharField(
        'Nome Completo',
        max_length=255,
        blank=True,
        null=True
    )
    whatsapp = models.CharField(
        'WhatsApp',
        max_length=20,  # Suficiente para formatos como +55 (11) 99999-9999
        blank=True,
        null=True,
        help_text='Número de WhatsApp para recuperação de senha.'
    )

    # Sobrescreve os campos herdados para desativar as constraints de FK no banco de dados,
    # permitindo relações entre bancos de dados diferentes (multi-tenant).
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text=(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="user_set",
        related_query_name="user",
        db_constraint=False  # Impede a criação da FK no banco de dados
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="user_set",
        related_query_name="user",
        db_constraint=False  # Impede a criação da FK no banco de dados
    )

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        swappable = 'AUTH_USER_MODEL'  # 🔁 Garante compatibilidade com settings.AUTH_USER_MODEL

    def __str__(self):
        return self.nome_completo or self.username

    def grupo_principal(self):
        """
        Retorna o primeiro grupo associado ao usuário (usando o campo 'groups' herdado).
        """
        return self.groups.first()

class GroupProfile(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='profile', db_constraint=False)
    is_active = models.BooleanField(default=True)
    finalidade = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.group.name

