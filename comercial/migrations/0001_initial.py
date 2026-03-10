from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='CondicaoPagamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=20, unique=True, verbose_name='Codigo')),
                ('descricao', models.CharField(max_length=120, verbose_name='Descricao')),
                ('quantidade_parcelas', models.PositiveIntegerField(default=1, verbose_name='Quantidade de Parcelas')),
                ('observacoes', models.TextField(blank=True, null=True, verbose_name='Observacoes')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Condicao de Pagamento',
                'verbose_name_plural': 'Condicoes de Pagamento',
                'ordering': ('codigo',),
            },
        ),
    ]
