# Generated by Django 4.2.15 on 2024-08-18 15:12

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cirtification',
            name='information',
        ),
        migrations.AddField(
            model_name='apk',
            name='apk_file',
            field=models.FileField(null=True, upload_to='apk_files/'),
        ),
        migrations.AddField(
            model_name='apk',
            name='apk_size',
            field=models.CharField(default='0B', max_length=20),
        ),
        migrations.AddField(
            model_name='apk',
            name='icon',
            field=models.ImageField(default='default.jpeg', upload_to='icons/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]),
        ),
        migrations.AddField(
            model_name='cirtification',
            name='end_time',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='cirtification',
            name='public_key_algorithm',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='cirtification',
            name='signature_algorithm',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='cirtification',
            name='start_time',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='cirtification',
            name='version',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='apk',
            name='md5_code',
            field=models.CharField(max_length=500, unique=True),
        ),
        migrations.AlterField(
            model_name='cirtification',
            name='sha1_code',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='cirtification',
            name='sha256_code',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
