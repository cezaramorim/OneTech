from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('control', '0005_alter_tenant_options'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SecurityAuditEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('AUTHZ_DENIED', 'Autorização negada'), ('SYSTEM', 'Evento de sistema')], db_index=True, max_length=32)),
                ('code', models.CharField(blank=True, db_index=True, default='', max_length=64)),
                ('detail', models.TextField(blank=True, default='')),
                ('method', models.CharField(blank=True, default='', max_length=16)),
                ('path', models.CharField(blank=True, db_index=True, default='', max_length=512)),
                ('host', models.CharField(blank=True, default='', max_length=255)),
                ('ip_address', models.CharField(blank=True, default='', max_length=64)),
                ('tenant_slug', models.CharField(blank=True, db_index=True, default='', max_length=128)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    'user',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='security_audit_events',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'verbose_name': 'Evento de Auditoria de Segurança',
                'verbose_name_plural': 'Eventos de Auditoria de Segurança',
                'ordering': ('-created_at',),
            },
        ),
    ]
