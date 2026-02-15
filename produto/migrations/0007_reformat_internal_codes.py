from django.db import migrations

def renumber_internal_codes(apps, schema_editor):
    """
    Recalcula todos os 'codigo_interno' para serem sequenciais,
    usando .update() para ignorar o método save() customizado.
    """
    Produto = apps.get_model('produto', 'Produto')
    db_alias = schema_editor.connection.alias
    
    # Ordena por chave primária para garantir uma ordem consistente
    produtos = Produto.objects.using(db_alias).all().order_by('pk')
    
    for i, produto in enumerate(produtos, 1):
        novo_codigo = f"{i:05d}"
        Produto.objects.using(db_alias).filter(pk=produto.pk).update(codigo_interno=novo_codigo)

class Migration(migrations.Migration):

    dependencies = [
        ('produto', '0006_fix_product_codes'),
    ]

    operations = [
        migrations.RunPython(renumber_internal_codes, migrations.RunPython.noop),
    ]
