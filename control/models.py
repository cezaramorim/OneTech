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

    emitente_padrao = models.ForeignKey(
        'control.Emitente',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='tenants',
        help_text="Emitente padrão associado a este tenant para operações fiscais."
    )

    # Controle
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Tenant (Cliente)"
        verbose_name_plural = "Tenants (Clientes)"


# ==============================================================================
# 🚀 MODELO DE EMITENTE (MATRIZ/FILIAIS)
# ==============================================================================
class Emitente(models.Model):
    """
    Armazena os dados de um emitente (matriz ou filial) que pode realizar
    operações fiscais. Cada tenant pode ter um ou mais emitentes.
    """
    razao_social = models.CharField("Razão Social", max_length=255)
    nome_fantasia = models.CharField("Nome Fantasia", max_length=255, blank=True, null=True)
    cnpj = models.CharField("CNPJ", max_length=18, unique=True) # CNPJ deve ser único por banco
    ie = models.CharField("Inscrição Estadual", max_length=20, blank=True, null=True)
    
    # Endereço
    cep = models.CharField("CEP", max_length=10, blank=True, null=True)
    logradouro = models.CharField("Logradouro", max_length=255, blank=True, null=True)
    numero = models.CharField("Número", max_length=20, blank=True, null=True)
    complemento = models.CharField("Complemento", max_length=255, blank=True, null=True)
    bairro = models.CharField("Bairro", max_length=100, blank=True, null=True)
    cidade = models.CharField("Cidade", max_length=100, blank=True, null=True)
    uf = models.CharField("UF", max_length=2, blank=True, null=True)

    # Contato
    telefone = models.CharField("Telefone", max_length=20, blank=True, null=True)
    email = models.EmailField("E-mail", blank=True, null=True)

    # Logo
    logotipo = models.ImageField("Logotipo", upload_to="logos_emitentes/", blank=True, null=True)

    # Configurações Adicionais
    is_default = models.BooleanField("Padrão", default=False, help_text="Marque se este é o emitente padrão para novas transações.")

    class Meta:
        verbose_name = "Emitente (Matriz/Filial)"
        verbose_name_plural = "Emitentes (Matriz/Filiais)"

    def __str__(self):
        return f"{self.nome_fantasia or self.razao_social} ({self.cnpj})"

    def save(self, *args, **kwargs):
        """
        Garante que apenas um emitente seja o padrão.
        """
        if self.is_default:
            # Desmarca todos os outros como padrão antes de salvar
            Emitente.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)