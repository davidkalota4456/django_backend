# Generated by Django 5.1.2 on 2024-12-05 15:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients_projects', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientproject',
            name='project_picture',
            field=models.ImageField(blank=True, null=True, upload_to='project_pictures/'),
        ),
    ]
