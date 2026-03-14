from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nota_fiscal', '0006_transportadora_alter_duplicatanotafiscal_numero_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='notafiscal',
            name='pre_emissao_ok',
            field=models.BooleanField(blank=True, null=True, verbose_name='Gate Pre-Emissao Aprovado'),
        ),
        migrations.AddField(
            model_name='notafiscal',
            name='pre_emissao_snapshot',
            field=models.JSONField(blank=True, null=True, verbose_name='Snapshot da Validacao Pre-Emissao'),
        ),
        migrations.AddField(
            model_name='notafiscal',
            name='pre_emissao_validada_em',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Data/Hora Validacao Pre-Emissao'),
        ),
    ]

