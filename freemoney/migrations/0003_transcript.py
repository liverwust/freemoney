# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-19 10:42
from __future__ import unicode_literals

from django.db import migrations, models
import freemoney.models.application


class Migration(migrations.Migration):

    dependencies = [
        ('freemoney', '0002_award_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='transcript',
            field=models.FileField(blank=True, null=True, upload_to=freemoney.models.application.upload_filename),
        ),
        migrations.AddField(
            model_name='application',
            name='transcript_modified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
