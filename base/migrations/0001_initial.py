# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='KeyValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ordering', models.IntegerField(default=0, verbose_name=b'\xe6\x8e\x92\xe5\xba\x8f\xe6\x9d\x83\xe5\x80\xbc', editable=False, db_index=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'\xe5\x88\x9b\xe5\xbb\xba\xe6\x97\xb6\xe9\x97\xb4')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name=b'\xe4\xbf\xae\xe6\x94\xb9\xe6\x97\xb6\xe9\x97\xb4')),
                ('key', models.CharField(unique=True, max_length=255, verbose_name=b'\xe5\x81\xa5', db_index=True)),
                ('type', models.CharField(default=b'text', max_length=255, null=True, verbose_name=b'\xe7\xb1\xbb\xe5\x9e\x8b', blank=True)),
                ('name', models.CharField(max_length=255, null=True, verbose_name=b'\xe5\x90\x8d\xe7\xa7\xb0', blank=True)),
                ('value', models.TextField(max_length=65535, null=True, verbose_name=b'\xe5\x80\xbc', blank=True)),
                ('other', models.CharField(max_length=255, null=True, verbose_name=b'\xe9\x99\x84\xe5\x8a\xa0', blank=True)),
            ],
            options={
                'ordering': ['ordering'],
                'verbose_name': '\u8bbe\u7f6e',
                'verbose_name_plural': '\u8bbe\u7f6e',
            },
        ),
    ]
