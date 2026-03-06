from django.db import migrations


def migrate_empresa_permissions(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')
    Group = apps.get_model('auth', 'Group')
    User = apps.get_model('accounts', 'User')

    old_ct = ContentType.objects.filter(app_label='empresas', model='empresaavancada').first()
    new_ct = ContentType.objects.filter(app_label='empresas', model='empresa').first()

    if old_ct is None or new_ct is None:
        return

    codename_map = {
        'add_empresaavancada': 'add_empresa',
        'change_empresaavancada': 'change_empresa',
        'delete_empresaavancada': 'delete_empresa',
        'view_empresaavancada': 'view_empresa',
    }

    old_perms = {
        perm.codename: perm
        for perm in Permission.objects.filter(content_type=old_ct)
    }
    new_perms = {
        perm.codename: perm
        for perm in Permission.objects.filter(content_type=new_ct)
    }

    group_permissions = Group.permissions.through
    user_permissions = User.user_permissions.through

    for old_codename, new_codename in codename_map.items():
        old_perm = old_perms.get(old_codename)
        new_perm = new_perms.get(new_codename)
        if old_perm is None or new_perm is None:
            continue

        group_ids = group_permissions.objects.filter(permission_id=old_perm.id).values_list('group_id', flat=True)
        for group_id in group_ids:
            group_permissions.objects.get_or_create(group_id=group_id, permission_id=new_perm.id)

        user_ids = user_permissions.objects.filter(permission_id=old_perm.id).values_list('user_id', flat=True)
        for user_id in user_ids:
            user_permissions.objects.get_or_create(user_id=user_id, permission_id=new_perm.id)

    Permission.objects.filter(content_type=old_ct).delete()
    old_ct.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0005_rename_empresaavancada_to_empresa'),
        ('nota_fiscal', '0003_update_empresa_relation_state'),
        ('produto', '0008_update_empresa_relation_state'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(
                    name='EmpresaAvancada',
                ),
            ],
            database_operations=[
                migrations.RunPython(migrate_empresa_permissions, migrations.RunPython.noop),
            ],
        ),
    ]
