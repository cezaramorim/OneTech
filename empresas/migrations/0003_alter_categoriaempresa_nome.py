# Generated by Django 5.1.7 on 2025-07-10 21:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0002_alter_empresaavancada_cnpj_alter_empresaavancada_cpf'),
    ]

    operations = [
        migrations.AlterField(
            model_name='categoriaempresa',
            name='nome',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
