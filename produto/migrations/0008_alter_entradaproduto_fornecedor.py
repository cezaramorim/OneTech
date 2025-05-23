# Generated by Django 5.1.7 on 2025-04-27 17:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0005_empresaavancada_categoria_empresaavancada_cliente_and_more'),
        ('produto', '0007_alter_produto_preco_custo_alter_produto_preco_medio_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entradaproduto',
            name='fornecedor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='entradas_fornecedor', to='empresas.empresaavancada'),
        ),
    ]
