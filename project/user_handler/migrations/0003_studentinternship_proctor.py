# Generated by Django 4.2.2 on 2024-06-29 07:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_handler', '0002_studentachievement_proctor'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentinternship',
            name='proctor',
            field=models.CharField(default=0, max_length=10),
            preserve_default=False,
        ),
    ]
