from django.db import models, transaction
from django.db.models import Max


class CondicaoPagamento(models.Model):
    codigo = models.PositiveIntegerField(unique=True, null=True, blank=True, editable=False, verbose_name='Codigo')
    descricao = models.CharField(max_length=120, verbose_name='Descricao')
    quantidade_parcelas = models.PositiveIntegerField(default=1, verbose_name='Quantidade de Parcelas')
    observacoes = models.TextField(blank=True, null=True, verbose_name='Observacoes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Condicao de Pagamento'
        verbose_name_plural = 'Condicoes de Pagamento'
        ordering = ('codigo',)

    def save(self, *args, **kwargs):
        self.descricao = ' '.join((self.descricao or '').strip().split())
        self.observacoes = ' '.join((self.observacoes or '').strip().split()) or None
        if not self.quantidade_parcelas or self.quantidade_parcelas < 1:
            self.quantidade_parcelas = 1

        if self.pk is None and not self.codigo:
            with transaction.atomic():
                ultimo_codigo = CondicaoPagamento.objects.select_for_update().aggregate(max_codigo=Max('codigo'))['max_codigo'] or 0
                self.codigo = int(ultimo_codigo) + 1
                return super().save(*args, **kwargs)

        if self.codigo:
            self.codigo = int(self.codigo)

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.codigo} - {self.descricao}'
