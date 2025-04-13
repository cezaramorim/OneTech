from django.db import models

# === Constantes de escolha para tipo e status da empresa ===
TIPO_EMPRESA_CHOICES = [
    ('Física', 'Física'),
    ('Jurídica', 'Jurídica'),
]

STATUS_CHOICES = [
    ('Ativa', 'Ativa'),
    ('Inativa', 'Inativa'),
]

# === Categoria de Empresa ===
class CategoriaEmpresa(models.Model):
    nome = models.CharField("Nome da Categoria", max_length=100, unique=True)

    def __str__(self):
        return self.nome


# === Modelo de Empresa ===
class Empresa(models.Model):
    # 🔹 Informações principais
    nome_empresa = models.CharField("Nome da Empresa", max_length=255)
    nome_fantasia = models.CharField("Nome Fantasia", max_length=255, blank=True, null=True)
    tipo_empresa = models.CharField("Tipo de Empresa", max_length=20, choices=TIPO_EMPRESA_CHOICES)
    cnae = models.CharField("CNAE", max_length=20)
    cnae_secundario = models.CharField("CNAE Secundário", max_length=20, blank=True, null=True)
    cnpj = models.CharField("CNPJ", max_length=20, unique=True)
    inscricao_estadual = models.CharField("Inscrição Estadual", max_length=20, blank=True, null=True)

    # 🔹 Endereço
    rua = models.CharField("Rua/Logradouro", max_length=255)
    numero = models.CharField("Número", max_length=20)
    complemento = models.CharField("Complemento", max_length=255, blank=True, null=True)
    bairro = models.CharField("Bairro", max_length=100)
    cidade = models.CharField("Cidade", max_length=100)
    estado = models.CharField("Estado/Região", max_length=100)
    cep = models.CharField("CEP/Código Postal", max_length=20)

    # 🔹 Contato
    telefone_principal = models.CharField("Telefone Principal", max_length=20)
    telefone_secundario = models.CharField("Telefone Secundário", max_length=20, blank=True, null=True)
    email_contato = models.EmailField("E-mail de contato", max_length=255)
    site = models.URLField("Site", max_length=255, blank=True, null=True)

    # 🔹 Representante
    nome_representante = models.CharField("Nome do Representante", max_length=255)
    celular_representante = models.CharField("Celular do Representante", max_length=20)
    email_representante = models.EmailField("E-mail do Representante", max_length=255)

    # 🔹 Extras
    data_cadastro = models.DateTimeField("Data de Cadastro", auto_now_add=True)
    status_empresa = models.CharField("Status da Empresa", max_length=10, choices=STATUS_CHOICES, default='Ativa')
    categoria = models.ForeignKey(CategoriaEmpresa, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.nome_empresa} ({self.cnpj})"
