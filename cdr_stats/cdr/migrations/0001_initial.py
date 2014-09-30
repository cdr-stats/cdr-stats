# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import caching.base
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='HangupCause',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.PositiveIntegerField(help_text='ITU-T Q.850 Code', unique=True, verbose_name='code')),
                ('enumeration', models.CharField(max_length=100, null=True, verbose_name='enumeration', blank=True)),
                ('cause', models.CharField(max_length=100, null=True, verbose_name='cause', blank=True)),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
            ],
            options={
                'db_table': 'hangup_cause',
                'verbose_name': 'hangupcause',
                'verbose_name_plural': 'hangupcauses',
            },
            bases=(caching.base.CachingMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Switch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, unique=True, null=True)),
                ('ipaddress', models.CharField(unique=True, max_length=100)),
                ('key_uuid', django_extensions.db.fields.UUIDField(editable=False, name=b'key_uuid', blank=True)),
            ],
            options={
                'db_table': 'voip_switch',
                'verbose_name': 'switch',
                'verbose_name_plural': 'switches',
            },
            bases=(caching.base.CachingMixin, models.Model),
        ),
    ]
