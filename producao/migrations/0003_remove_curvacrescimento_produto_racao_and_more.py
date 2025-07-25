# Generated by Django 5.1.7 on 2025-07-21 22:17

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('producao', '0002_curvacrescimento_lote_alimentacaodiaria_tanque_and_more'),
        ('produto', '0004_remove_produto_descricao'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='curvacrescimento',
            name='produto_racao',
        ),
        migrations.AddField(
            model_name='curvacrescimento',
            name='especie',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='curvacrescimento',
            name='rendimento_carcaca',
            field=models.DecimalField(decimal_places=2, default=100.0, help_text='Percentual de rendimento de carcaça (ex: 85.50 para 85.5%)', max_digits=5),
        ),
        migrations.AlterField(
            model_name='curvacrescimento',
            name='nome',
            field=models.CharField(help_text="Nome único para a curva, ex: 'Curva Tilápia Outono 2025'", max_length=255, unique=True),
        ),
        migrations.CreateModel(
            name='DetalheCurvaCrescimento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('periodo', models.IntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('dias', models.IntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('peso_inicial', models.DecimalField(decimal_places=4, max_digits=10)),
                ('peso_final', models.DecimalField(decimal_places=4, max_digits=10)),
                ('ganho_peso', models.DecimalField(decimal_places=4, max_digits=10)),
                ('numero_tratos', models.IntegerField()),
                ('hora_inicio_trato', models.TimeField()),
                ('arracoamento_biomassa', models.DecimalField(decimal_places=2, help_text='Percentual de arraçoamento sobre a biomassa (ex: 10.30 para 10.3%)', max_digits=5)),
                ('mortalidade_presumida', models.DecimalField(decimal_places=2, help_text='Percentual de mortalidade presumida ao dia (ex: 0.30 para 0.3%)', max_digits=5)),
                ('gpd', models.DecimalField(decimal_places=4, max_digits=10, verbose_name='GPD (Ganho de Peso Diário)')),
                ('tca', models.DecimalField(decimal_places=4, max_digits=10, verbose_name='TCA (Taxa de Conversão Alimentar)')),
                ('curva', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalhes', to='producao.curvacrescimento')),
                ('racao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='produto.produto')),
            ],
            options={
                'verbose_name': 'Detalhe da Curva de Crescimento',
                'verbose_name_plural': 'Detalhes da Curva de Crescimento',
                'ordering': ['periodo'],
                'unique_together': {('curva', 'periodo')},
            },
        ),
    ]
