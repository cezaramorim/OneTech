from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0003_alter_categoriaempresa_nome'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Empresa',
        ),
    ]
