# Generated by Django 4.2.23 on 2025-07-27 11:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_customuser_blocked_msg_customuser_id_blocked'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='id_blocked',
        ),
        migrations.AddField(
            model_name='customuser',
            name='is_blocked',
            field=models.BooleanField(default=False, verbose_name='Is Blocked'),
        ),
    ]
