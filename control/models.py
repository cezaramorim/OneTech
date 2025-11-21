# control/models.py
from django.db import models
from .utils import tenant_media_path
from .utils import tenant_media_path

class Tenant(models.Model):
    # Identificação e Conexão
    nome = models.CharField(max_length=150, help_text="Nome comercial do cliente/tenant")
    slug = models.SlugField(unique=True, help_text="Identificador único para URLs e diretórios (e.g., 'cliente-a')")
    dominio = models.CharField(max_length=255, unique=True, help_text="Domínio ou subdomínio para acesso (e.g., 'cliente-a.onetech.app')")
    
    # Credenciais do Banco de Dados (armazenar de forma segura em produção, e.g., Vault)
    db_name = models.CharField(max_length=100, unique=True)
    db_user = models.CharField(max_length=100)
    db_password = models.CharField(max_length=100)
    db_host = models.CharField(max_length=100, default="127.0.0.1")
    db_port = models.CharField(max_length=10, default="3306")

    # Branding e Dados da Empresa para NF-e
    razao_social = models.CharField(max_length=255)
    nome_fantasia = models.CharField(max_length=255, blank=True)
    cnpj = models.CharField(max_length=18, help_text="Formato: XX.XXX.XXX/XXXX-XX")
    ie = models.CharField("Inscrição Estadual", max_length=20, blank=True)
    logo = models.ImageField(upload_to=tenant_media_path, blank=True, null=True)

    # Configurações de NF-e (A1)
    certificado_a1 = models.FileField(upload_to=tenant_media_path, blank=True, null=True, help_text="Arquivo .pfx ou .p12")
    senha_certificado = models.CharField(max_length=128, blank=True, help_text="Senha do arquivo de certificado digital")
    
    # CSC (Código de Segurança do Contribuinte) para NFC-e
    csc = models.CharField("CSC/Token", max_length=64, blank=True)
    id_token = models.CharField("ID do Token CSC", max_length=32, blank=True)

    # Controle
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Tenant (Cliente)"
        verbose_name_plural = "Tenants (Clientes)"