# Generated by Django 5.1.7 on 2025-03-23 22:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_user_options_alter_user_nome_completo'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='grupos',
            field=models.ManyToManyField(blank=True, related_name='usuarios', to='auth.group', verbose_name='Grupos'),
        ),
    ]
