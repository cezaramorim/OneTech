from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0006_remove_empresaavancada_proxy_and_permissions'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='empresa',
            table='empresas_empresa',
        ),
    ]
