from django.db import models
from django.contrib.auth import get_user_model

# === Categorias ===
class CategoriaEmpresa(models.Model):
   nome = models.CharField(max_length=100)

   def __str__(self):
       return self.nome

# === Empresa Simples (padrão existente) ===
class Empresa(models.Model):
    nome_empresa = models.CharField(max_length=255)
    nome_fantasia = models.CharField(max_length=255, blank=True, null=True)
    tipo_empresa = models.CharField(max_length=10, choices=[('pj', 'Pessoa Jurídica'), ('pf', 'Pessoa Física')])
    cnae = models.CharField(max_length=20, blank=True, null=True)
    cnae_secundario = models.CharField(max_length=20, blank=True, null=True)
    cnpj = models.CharField(max_length=20, blank=True, null=True)
    inscricao_estadual = models.CharField(max_length=20, blank=True, null=True)

    rua = models.CharField(max_length=255, blank=True, null=True)
    numero = models.CharField(max_length=20, blank=True, null=True)
    complemento = models.CharField(max_length=255, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    cep = models.CharField(max_length=10, blank=True, null=True)

    telefone_principal = models.CharField(max_length=20, blank=True, null=True)
    telefone_secundario = models.CharField(max_length=20, blank=True, null=True)
    email_contato = models.EmailField(blank=True, null=True)
    site = models.URLField(blank=True, null=True)

    nome_representante = models.CharField(max_length=100, blank=True, null=True)
    celular_representante = models.CharField(max_length=20, blank=True, null=True)
    email_representante = models.EmailField(blank=True, null=True)
    
    status_empresa = models.CharField(max_length=20, choices=[('ativa', 'Ativa'), ('inativa', 'Inativa')], default='ativa')
    categoria = models.ForeignKey(CategoriaEmpresa, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nome_empresa



# === Empresa Avançada ===
class EmpresaAvancada(models.Model):
    tipo_empresa = models.CharField(max_length=10, choices=[('pj', 'Pessoa Jurídica'), ('pf', 'Pessoa Física')])

    # Pessoa Jurídica
    razao_social = models.CharField(max_length=255, blank=True, null=True)
    nome_fantasia = models.CharField(max_length=255, blank=True, null=True)
    cnpj = models.CharField(max_length=20, blank=True, null=True)
    ie = models.CharField("Inscrição Estadual", max_length=20, blank=True, null=True)

    # Pessoa Física
    nome = models.CharField(max_length=255, blank=True, null=True)
    cpf = models.CharField(max_length=20, blank=True, null=True)
    rg = models.CharField(max_length=20, blank=True, null=True)
    profissao = models.CharField(max_length=100, blank=True, null=True)

    # CNAE e datas
    cnae_principal = models.CharField(max_length=20, blank=True, null=True)
    cnae_secundario = models.CharField(max_length=20, blank=True, null=True)
    data_abertura = models.DateField(blank=True, null=True)
    data_cadastro = models.DateField(auto_now_add=True)

    # Endereço
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
    
    # Contato Financeiro
    contato_financeiro_nome = models.CharField(max_length=255, blank=True, null=True)
    contato_financeiro_email = models.EmailField(blank=True, null=True)
    contato_financeiro_telefone = models.CharField(max_length=20, blank=True, null=True)
    contato_financeiro_celular = models.CharField(max_length=20, blank=True, null=True)

    # Contato Comercial
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
    status_empresa = models.CharField(max_length=20, choices=[('ativa', 'Ativa'), ('inativa', 'Inativa')], default='ativa')
    categoria = models.ForeignKey(CategoriaEmpresa, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.razao_social or self.nome or 'Empresa Avançada'
