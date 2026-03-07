from django.db import migrations
import uuid


def populate_missing_internal_codes(apps, schema_editor):
    """
    Garante que todo produto tenha codigo_interno.
    Nao depende da coluna legada 'codigo', que ja foi removida na migracao 0004.
    """
    Produto = apps.get_model('produto', 'Produto')
    db_alias = schema_editor.connection.alias

    for produto in Produto.objects.using(db_alias).all():
        if not produto.codigo_interno:
            produto.codigo_interno = str(uuid.uuid4()).replace('-', '')[:20].upper()
            produto.save(update_fields=['codigo_interno'])


class Migration(migrations.Migration):

    dependencies = [
        ('produto', '0005_alter_produto_codigo_interno'),
    ]

    operations = [
        migrations.RunPython(populate_missing_internal_codes, migrations.RunPython.noop),
    ]
