# Generated by Django 5.1.7 on 2025-04-27 18:06

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nota_fiscal', '0002_alter_notafiscal_fornecedor'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='notafiscal',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notas_criadas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='transportenotafiscal',
            name='modalidade_frete',
            field=models.CharField(blank=True, choices=[('0', 'CIF'), ('1', 'FOB'), ('2', 'Terceiros'), ('9', 'Sem transporte')], max_length=2, null=True),
        ),
    ]
