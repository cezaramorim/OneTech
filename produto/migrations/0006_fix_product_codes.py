from django.db import migrations, models
import uuid

def copy_data_and_populate_interno(apps, schema_editor):
    """
    Copia dados da coluna 'codigo' para 'codigo_fornecedor' e popula 'codigo_interno'.
    Usa SQL bruto para interagir com a coluna 'codigo' que não existe no modelo Django.
    """
    db_alias = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        # Copia os dados de 'codigo' para 'codigo_fornecedor' onde este último estiver vazio
        cursor.execute("""
            UPDATE produto_produto
            SET codigo_fornecedor = codigo
            WHERE codigo_fornecedor IS NULL OR codigo_fornecedor = ''
        """)

    # Popula o codigo_interno usando o modelo Django
    Produto = apps.get_model('produto', 'Produto')
    for produto in Produto.objects.using(db_alias).all():
        if not produto.codigo_interno:
            produto.codigo_interno = str(uuid.uuid4()).replace('-', '')[:20].upper()
            produto.save(update_fields=['codigo_interno'])

class Migration(migrations.Migration):

    dependencies = [
        ('produto', '0005_alter_produto_codigo_interno'),
    ]

    operations = [
        # Passo 1: Adicionar a coluna codigo_interno primeiro, se ela não existir.
        # A migração 0005 já faz isso, mas vamos garantir.
        # O campo já existe no modelo, então o Django vai gerenciá-lo.
        
        # Passo 2: Copiar os dados da coluna 'codigo' para 'codigo_fornecedor'
        # e popular o 'codigo_interno' para todos os registros.
        migrations.RunPython(copy_data_and_populate_interno, migrations.RunPython.noop),

        # Passo 3: Remover a coluna 'codigo' antiga, que agora é redundante.
        migrations.RunSQL(
            "ALTER TABLE produto_produto DROP COLUMN codigo;",
            "ALTER TABLE produto_produto ADD COLUMN codigo VARCHAR(50);"
        ),
    ]
