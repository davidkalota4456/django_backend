# Generated by Django 5.1.2 on 2024-12-27 06:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients_projects', '0004_clientproject_creation_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientproject',
            name='start_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
