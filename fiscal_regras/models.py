import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from fiscal.models import CST, CSOSN

from .constants import MODALIDADE_CHOICES, TIPO_OPERACAO_CHOICES
from .validators import validate_ncm_prefixo


class RegraAliquotaICMS(models.Model):
    ativo = models.BooleanField(default=True)
    descricao = models.CharField(max_length=255)
    ncm_prefixo = models.CharField(max_length=8, validators=[validate_ncm_prefixo])
    prefixo_len = models.PositiveSmallIntegerField(editable=False)

    tipo_operacao = models.CharField(max_length=1, choices=TIPO_OPERACAO_CHOICES, blank=True, null=True)
    modalidade = models.CharField(max_length=20, choices=MODALIDADE_CHOICES, blank=True, null=True)

    uf_origem = models.CharField(max_length=2, blank=True, null=True)
    uf_destino = models.CharField(max_length=2, blank=True, null=True)
    origem_mercadoria = models.CharField(max_length=1, blank=True, null=True)

    cst_icms = models.ForeignKey(CST, on_delete=models.SET_NULL, null=True, blank=True, related_name='regras_icms_cst')
    csosn_icms = models.ForeignKey(CSOSN, on_delete=models.SET_NULL, null=True, blank=True, related_name='regras_icms_csosn')

    aliquota_icms = models.DecimalField(max_digits=5, decimal_places=2)
    fcp = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    reducao_base_icms = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    prioridade = models.IntegerField(default=0)
    vigencia_inicio = models.DateField(default=timezone.localdate)
    vigencia_fim = models.DateField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='regras_aliquota_icms_criadas',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='regras_aliquota_icms_atualizadas',
    )

    class Meta:
        verbose_name = 'Regra de Aliquota ICMS'
        verbose_name_plural = 'Regras de Aliquota ICMS'
        ordering = ['-ativo', '-prioridade', '-prefixo_len', 'descricao']
        indexes = [
            models.Index(fields=['ativo', 'vigencia_inicio', 'vigencia_fim']),
            models.Index(fields=['ncm_prefixo', 'prefixo_len']),
            models.Index(fields=['modalidade', 'uf_origem', 'uf_destino']),
            models.Index(fields=['tipo_operacao', 'prioridade']),
        ]
        permissions = [
            ('override_aliquota_item', 'Pode sobrescrever aliquota automatica do item'),
        ]

    def clean(self):
        self.ncm_prefixo = re.sub(r'\D', '', str(self.ncm_prefixo or ''))
        validate_ncm_prefixo(self.ncm_prefixo)
        self.prefixo_len = len(self.ncm_prefixo)

        self.uf_origem = (self.uf_origem or '').strip().upper() or None
        self.uf_destino = (self.uf_destino or '').strip().upper() or None
        self.origem_mercadoria = (self.origem_mercadoria or '').strip() or None

        if self.vigencia_fim and self.vigencia_fim < self.vigencia_inicio:
            raise ValidationError({'vigencia_fim': 'Vigencia fim nao pode ser anterior a vigencia inicio.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.ncm_prefixo} | {self.descricao}'
