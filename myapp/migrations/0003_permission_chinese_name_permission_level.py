# Generated by Django 4.2.15 on 2024-08-18 16:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0002_remove_cirtification_information_apk_apk_file_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='permission',
            name='chinese_name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='permission',
            name='level',
            field=models.IntegerField(default=0),
        ),
    ]