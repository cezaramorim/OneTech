import re

from django.db import models


def _collapse_spaces(value):
    return re.sub(r'\s+', ' ', (value or '').strip())


class Cfop(models.Model):
    codigo = models.CharField(max_length=4, unique=True, verbose_name='C\u00f3digo CFOP')
    descricao = models.TextField(verbose_name='Descri\u00e7\u00e3o')
    categoria = models.CharField(max_length=100, blank=True, null=True, verbose_name='Categoria')

    class Meta:
        verbose_name = 'CFOP'
        verbose_name_plural = 'CFOPs'
        ordering = ['codigo']

    def save(self, *args, **kwargs):
        self.codigo = re.sub(r'\D', '', str(self.codigo or ''))[:4]
        self.descricao = _collapse_spaces(self.descricao)
        self.categoria = _collapse_spaces(self.categoria) or None
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.codigo} - {self.descricao}'


class NaturezaOperacao(models.Model):
    codigo = models.CharField(max_length=10, unique=True, blank=True, null=True, verbose_name='C\u00f3digo Interno')
    descricao = models.TextField(verbose_name='Descri\u00e7\u00e3o da Natureza de Opera\u00e7\u00e3o')
    observacoes = models.TextField(blank=True, null=True, verbose_name='Observa\u00e7\u00f5es')

    class Meta:
        verbose_name = 'Natureza de Opera\u00e7\u00e3o'
        verbose_name_plural = 'Naturezas de Opera\u00e7\u00e3o'
        ordering = ['descricao']

    def save(self, *args, **kwargs):
        self.codigo = _collapse_spaces(str(self.codigo or '')).upper() or None
        self.descricao = _collapse_spaces(self.descricao)
        self.observacoes = _collapse_spaces(self.observacoes) or None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.descricao


class CST(models.Model):
    codigo = models.CharField(max_length=2, unique=True, verbose_name='C\u00f3digo CST')
    descricao = models.TextField(verbose_name='Descri\u00e7\u00e3o')

    class Meta:
        verbose_name = 'CST'
        verbose_name_plural = 'CSTs'
        ordering = ['codigo']

    def __str__(self):
        return f'{self.codigo} - {self.descricao}'


class CSOSN(models.Model):
    codigo = models.CharField(max_length=3, unique=True, verbose_name='C\u00f3digo CSOSN')
    descricao = models.TextField(verbose_name='Descri\u00e7\u00e3o')

    class Meta:
        verbose_name = 'CSOSN'
        verbose_name_plural = 'CSOSNs'
        ordering = ['codigo']

    def __str__(self):
        return f'{self.codigo} - {self.descricao}'
