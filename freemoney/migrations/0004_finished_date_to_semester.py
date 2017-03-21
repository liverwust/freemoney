# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-21 14:24
from __future__ import unicode_literals

from django.db import migrations
import freemoney.models.semester


class Migration(migrations.Migration):

    dependencies = [
        ('freemoney', '0003_no_feedback'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='financialaid',
            name='end_date',
        ),
        migrations.AddField(
            model_name='financialaid',
            name='semester_finished',
            field=freemoney.models.semester.SemesterField(blank=True, null=True),
        ),
    ]
