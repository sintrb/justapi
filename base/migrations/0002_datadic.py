# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import base.fields


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataDic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ordering', models.IntegerField(default=0, verbose_name=b'\xe6\x8e\x92\xe5\xba\x8f\xe6\x9d\x83\xe5\x80\xbc', editable=False, db_index=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'\xe5\x88\x9b\xe5\xbb\xba\xe6\x97\xb6\xe9\x97\xb4')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name=b'\xe4\xbf\xae\xe6\x94\xb9\xe6\x97\xb6\xe9\x97\xb4')),
                ('status', models.IntegerField(default=0, verbose_name=b'\xe7\x8a\xb6\xe6\x80\x81', editable=False, choices=[(0, b'\xe6\xad\xa3\xe5\xb8\xb8'), (-1, b'\xe5\xb7\xb2\xe9\x94\x81\xe5\xae\x9a')])),
                ('type', models.CharField(max_length=255, verbose_name=b'\xe7\xb1\xbb\xe5\x9e\x8b', db_index=True)),
                ('value', models.CharField(max_length=255, verbose_name=b'\xe6\x95\xb0\xe6\x8d\xae', db_index=True)),
                ('json', base.fields.JsonField(default={}, max_length=65535, blank=True, help_text=b'', null=True, verbose_name=b'\xe9\x99\x84\xe5\x8a\xa0')),
            ],
            options={
                'ordering': ['ordering'],
                'verbose_name': '\u6570\u636e\u5b57\u5178',
                'verbose_name_plural': '\u6570\u636e\u5b57\u5178',
            },
        ),
    ]
