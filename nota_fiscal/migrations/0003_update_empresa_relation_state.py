import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0005_rename_empresaavancada_to_empresa'),
        ('nota_fiscal', '0002_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='notafiscal',
                    name='destinatario',
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='notas_recebidas',
                        to='empresas.empresa',
                        verbose_name='Destinatário (Cliente)',
                    ),
                ),
                migrations.AlterField(
                    model_name='notafiscal',
                    name='emitente',
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='notas_emitidas_por_terceiros',
                        to='empresas.empresa',
                        verbose_name='Emitente (Fornecedor)',
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]
