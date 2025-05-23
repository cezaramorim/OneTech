# Generated by Django 5.1.7 on 2025-04-18 18:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0004_remove_empresa_data_cadastro_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='empresaavancada',
            name='categoria',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='empresas.categoriaempresa'),
        ),
        migrations.AddField(
            model_name='empresaavancada',
            name='cliente',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='empresaavancada',
            name='contato_comercial_celular',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='empresaavancada',
            name='contato_comercial_email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='empresaavancada',
            name='contato_comercial_nome',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='empresaavancada',
            name='contato_comercial_telefone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='empresaavancada',
            name='contato_financeiro_celular',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='empresaavancada',
            name='contato_financeiro_email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='empresaavancada',
            name='contato_financeiro_nome',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='empresaavancada',
            name='contato_financeiro_telefone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='empresaavancada',
            name='fornecedor',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='empresaavancada',
            name='status_empresa',
            field=models.CharField(choices=[('ativa', 'Ativa'), ('inativa', 'Inativa')], default='ativa', max_length=20),
        ),
    ]
