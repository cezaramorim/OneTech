import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0005_rename_empresaavancada_to_empresa'),
        ('produto', '0007_reformat_internal_codes'),
        ('nota_fiscal', '0003_update_empresa_relation_state'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='entradaproduto',
                    name='fornecedor',
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='entradas_produto',
                        to='empresas.empresa',
                    ),
                ),
                migrations.AlterField(
                    model_name='produto',
                    name='fornecedor',
                    field=models.ForeignKey(
                        blank=True,
                        help_text='Empresa fornecedora vinculada via XML da nota fiscal.',
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='produtos_fornecidos',
                        to='empresas.empresa',
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]
