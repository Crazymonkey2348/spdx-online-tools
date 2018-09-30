# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-09-30 19:52
from __future__ import unicode_literals

import api.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CheckLicenseFileUpload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('file', models.FileField(upload_to=api.models.user_directory_path)),
                ('result', models.CharField(max_length=128)),
                ('status', models.IntegerField(default=200)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CompareFileUpload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('result', models.CharField(max_length=32)),
                ('message', models.CharField(max_length=64)),
                ('file1', models.FileField(upload_to=api.models.user_directory_path)),
                ('file2', models.FileField(upload_to=api.models.user_directory_path)),
                ('rfilename', models.CharField(max_length=32)),
                ('status', models.IntegerField(default=200)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ConvertFileUpload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('from_format', models.CharField(max_length=16)),
                ('to_format', models.CharField(max_length=16)),
                ('tagToRdfFormat', models.CharField(blank=True, max_length=16, null=True)),
                ('cfilename', models.CharField(max_length=32)),
                ('result', models.CharField(max_length=32)),
                ('message', models.CharField(max_length=64)),
                ('file', models.FileField(upload_to=api.models.user_directory_path)),
                ('status', models.IntegerField(default=200)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ValidateFileUpload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('file', models.FileField(upload_to=api.models.user_directory_path)),
                ('result', models.CharField(max_length=128)),
                ('status', models.IntegerField(default=200)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
