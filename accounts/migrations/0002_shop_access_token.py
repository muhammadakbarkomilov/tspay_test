# Generated by Django 4.2 on 2025-07-24 19:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='shop',
            name='access_token',
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
    ]
