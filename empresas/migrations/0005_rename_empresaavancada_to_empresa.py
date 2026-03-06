from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0004_remove_empresa_state_only'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RenameModel(
                    old_name='EmpresaAvancada',
                    new_name='Empresa',
                ),
                migrations.AlterModelTable(
                    name='empresa',
                    table='empresas_empresaavancada',
                ),
                migrations.AlterModelOptions(
                    name='empresa',
                    options={'verbose_name': 'Empresa', 'verbose_name_plural': 'Empresas'},
                ),
                migrations.CreateModel(
                    name='EmpresaAvancada',
                    fields=[],
                    options={'proxy': True, 'verbose_name': 'Empresa', 'verbose_name_plural': 'Empresas'},
                    bases=('empresas.empresa',),
                ),
            ],
            database_operations=[],
        ),
    ]
