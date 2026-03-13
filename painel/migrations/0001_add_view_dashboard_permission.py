from django.db import migrations


def criar_permissao_dashboard(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')

    content_type, _ = ContentType.objects.get_or_create(
        app_label='painel',
        model='dashboardaccess',
    )

    Permission.objects.get_or_create(
        content_type=content_type,
        codename='view_dashboard',
        defaults={'name': 'Can view dashboard'},
    )


def remover_permissao_dashboard(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')

    try:
        content_type = ContentType.objects.get(app_label='painel', model='dashboardaccess')
    except ContentType.DoesNotExist:
        return

    Permission.objects.filter(content_type=content_type, codename='view_dashboard').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(criar_permissao_dashboard, remover_permissao_dashboard),
    ]
