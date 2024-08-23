# Generated by Django 4.2.15 on 2024-08-19 08:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0004_apk_conclusion'),
    ]

    operations = [
        migrations.AddField(
            model_name='apk',
            name='code_result',
            field=models.CharField(default='正常', max_length=20),
        ),
        migrations.AddField(
            model_name='apk',
            name='confidence_level',
            field=models.CharField(default='1', max_length=50),
        ),
    ]
