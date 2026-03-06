from django.contrib.auth import get_user_model
from django.db import models


class CategoriaEmpresa(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome


# Modelo oficial do fluxo atual.
class Empresa(models.Model):
    """Cadastro completo de empresas para o fluxo atual do sistema."""

    tipo_empresa = models.CharField(max_length=10, choices=[('pj', 'Pessoa Jurídica'), ('pf', 'Pessoa Física')])

    # Pessoa juridica
    razao_social = models.CharField(max_length=255, blank=True, null=True)
    nome_fantasia = models.CharField(max_length=255, blank=True, null=True)
    cnpj = models.CharField(max_length=20, unique=True, blank=True, null=True)
    ie = models.CharField('Inscrição Estadual', max_length=20, blank=True, null=True)

    # Dados fiscais
    regime_tributario = models.CharField(
        max_length=2,
        choices=[
            ('SN', 'Simples Nacional'),
            ('LP', 'Lucro Presumido'),
            ('LR', 'Lucro Real'),
        ],
        blank=True,
        null=True,
        verbose_name='Regime Tributário',
        help_text='Regime tributário da empresa para fins fiscais.',
    )
    contribuinte_icms = models.BooleanField(
        default=False,
        verbose_name='Contribuinte ICMS',
        help_text='Indica se a empresa é contribuinte do ICMS.',
    )
    inscricao_municipal = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Inscrição Municipal',
        help_text='Inscrição Municipal da empresa (para serviços).',
    )

    # Pessoa fisica
    nome = models.CharField(max_length=255, blank=True, null=True)
    cpf = models.CharField(max_length=20, unique=True, blank=True, null=True)
    rg = models.CharField(max_length=20, blank=True, null=True)
    profissao = models.CharField(max_length=100, blank=True, null=True)

    # CNAE e datas
    cnae_principal = models.CharField(max_length=20, blank=True, null=True)
    cnae_secundario = models.CharField(max_length=20, blank=True, null=True)
    data_abertura = models.DateField(blank=True, null=True)
    data_cadastro = models.DateField(auto_now_add=True)

    # Endereco
    cep = models.CharField(max_length=10, blank=True, null=True)
    logradouro = models.CharField(max_length=255, blank=True, null=True)
    numero = models.CharField(max_length=20, blank=True, null=True)
    complemento = models.CharField(max_length=255, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    uf = models.CharField(max_length=2, blank=True, null=True)

    # Contato
    telefone = models.CharField(max_length=20, blank=True, null=True)
    celular = models.CharField(max_length=20, blank=True, null=True)
    whatsapp = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    site = models.URLField(blank=True, null=True)

    # Contato financeiro
    contato_financeiro_nome = models.CharField(max_length=255, blank=True, null=True)
    contato_financeiro_email = models.EmailField(blank=True, null=True)
    contato_financeiro_telefone = models.CharField(max_length=20, blank=True, null=True)
    contato_financeiro_celular = models.CharField(max_length=20, blank=True, null=True)

    # Contato comercial
    contato_comercial_nome = models.CharField(max_length=255, blank=True, null=True)
    contato_comercial_email = models.EmailField(blank=True, null=True)
    contato_comercial_telefone = models.CharField(max_length=20, blank=True, null=True)
    contato_comercial_celular = models.CharField(max_length=20, blank=True, null=True)

    # Comercial
    condicao_pagamento = models.CharField(max_length=255, blank=True, null=True)
    comissao = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    vendedor = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)

    # Relacionamentos e controle
    cliente = models.BooleanField(default=False)
    fornecedor = models.BooleanField(default=False)
    status_empresa = models.CharField(
        max_length=20,
        choices=[('ativa', 'Ativa'), ('inativa', 'Inativa')],
        default='ativa',
    )
    categoria = models.ForeignKey(CategoriaEmpresa, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'empresas_empresa'
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'

    def __str__(self):
        return self.razao_social or self.nome or 'Empresa'

