from django.db import models

class Cfop(models.Model):
    codigo = models.CharField(max_length=4, unique=True, verbose_name="Código CFOP")
    descricao = models.TextField(verbose_name="Descrição")
    categoria = models.CharField(max_length=100, blank=True, null=True, verbose_name="Categoria")

    class Meta:
        verbose_name = "CFOP"
        verbose_name_plural = "CFOPs"
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"

class NaturezaOperacao(models.Model):
    codigo = models.CharField(max_length=10, unique=True, blank=True, null=True, verbose_name="Código Interno")
    descricao = models.TextField(verbose_name="Descrição da Natureza de Operação")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")

    class Meta:
        verbose_name = "Natureza de Operação"
        verbose_name_plural = "Naturezas de Operação"
        ordering = ['descricao']

    def __str__(self):
        return self.descricao