# Generated by Django 5.1.7 on 2025-03-23 19:35

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Empresa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_empresa', models.CharField(max_length=255, verbose_name='Nome da Empresa')),
                ('nome_fantasia', models.CharField(blank=True, max_length=255, null=True, verbose_name='Nome Fantasia')),
                ('tipo_empresa', models.CharField(choices=[('Física', 'Física'), ('Jurídica', 'Jurídica')], max_length=20, verbose_name='Tipo de Empresa')),
                ('cnae', models.CharField(max_length=20, verbose_name='CNAE')),
                ('cnae_secundario', models.CharField(blank=True, max_length=20, null=True, verbose_name='CNAE Secundário')),
                ('cnpj', models.CharField(max_length=20, unique=True, verbose_name='CNPJ')),
                ('inscricao_estadual', models.CharField(blank=True, max_length=20, null=True, verbose_name='Inscrição Estadual')),
                ('rua', models.CharField(max_length=255, verbose_name='Rua/Logradouro')),
                ('numero', models.CharField(max_length=20, verbose_name='Número')),
                ('complemento', models.CharField(blank=True, max_length=255, null=True, verbose_name='Complemento')),
                ('bairro', models.CharField(max_length=100, verbose_name='Bairro')),
                ('cidade', models.CharField(max_length=100, verbose_name='Cidade')),
                ('estado', models.CharField(max_length=100, verbose_name='Estado/Região')),
                ('cep', models.CharField(max_length=20, verbose_name='CEP/Código Postal')),
                ('telefone_principal', models.CharField(max_length=20, verbose_name='Telefone Principal')),
                ('telefone_secundario', models.CharField(blank=True, max_length=20, null=True, verbose_name='Telefone Secundário')),
                ('email_contato', models.EmailField(max_length=255, verbose_name='E-mail de contato')),
                ('site', models.URLField(blank=True, max_length=255, null=True, verbose_name='Site')),
                ('nome_representante', models.CharField(max_length=255, verbose_name='Nome do Representante')),
                ('celular_representante', models.CharField(max_length=20, verbose_name='Celular do Representante')),
                ('email_representante', models.EmailField(max_length=255, verbose_name='E-mail do Representante')),
                ('data_cadastro', models.DateTimeField(auto_now_add=True, verbose_name='Data de Cadastro')),
                ('status_empresa', models.CharField(choices=[('Ativa', 'Ativa'), ('Inativa', 'Inativa')], default='Ativa', max_length=10, verbose_name='Status da Empresa')),
            ],
        ),
    ]
