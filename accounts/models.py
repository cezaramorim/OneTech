from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    nome_completo = models.CharField(
        'Nome Completo',
        max_length=255,
        blank=True,
        null=True
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

