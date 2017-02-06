# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-06 23:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import fm_apply.models
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activity_type', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=255)),
                ('accomplishments', models.CharField(max_length=255)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='ApplicantResponse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('submitted', models.BooleanField(default=False)),
                ('name', models.CharField(blank=True, max_length=255)),
                ('address', models.TextField(blank=True)),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128)),
                ('psu_email', models.EmailField(blank=True, max_length=254)),
                ('preferred_email', models.EmailField(blank=True, max_length=254)),
                ('psu_id', models.CharField(blank=True, max_length=9)),
                ('semester_initiated', fm_apply.models.SemesterField(null=True)),
                ('semester_graduating', fm_apply.models.SemesterField(null=True)),
                ('cumulative_gpa', models.DecimalField(decimal_places=2, max_digits=3, null=True)),
                ('semester_gpa', models.DecimalField(decimal_places=2, max_digits=3, null=True)),
                ('in_state_tuition', models.NullBooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='EssayPrompt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permanent_id', models.SlugField(unique=True)),
                ('created_timestamp', models.DateTimeField()),
                ('prompt', models.TextField()),
                ('previous_version', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='fm_apply.EssayPrompt')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EssayResponse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('prompt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fm_apply.EssayPrompt')),
                ('response', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fm_apply.ApplicantResponse')),
            ],
        ),
        migrations.CreateModel(
            name='FinancialAidRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aid_type', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=255)),
                ('amount_per_year', models.DecimalField(decimal_places=2, max_digits=7)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('response', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fm_apply.ApplicantResponse')),
            ],
        ),
        migrations.CreateModel(
            name='ScholarshipAward',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permanent_id', models.SlugField(unique=True)),
                ('created_timestamp', models.DateTimeField()),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('previous_version', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='fm_apply.ScholarshipAward')),
                ('response_set', models.ManyToManyField(to='fm_apply.ApplicantResponse')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='essayprompt',
            name='response_set',
            field=models.ManyToManyField(through='fm_apply.EssayResponse', to='fm_apply.ApplicantResponse'),
        ),
        migrations.AddField(
            model_name='activityrecord',
            name='response',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fm_apply.ApplicantResponse'),
        ),
    ]
