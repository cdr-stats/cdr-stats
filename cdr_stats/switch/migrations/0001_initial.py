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
            name='Switch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, unique=True, null=True)),
                ('ipaddress', models.CharField(unique=True, max_length=100)),
                ('switch_type', models.IntegerField(default=4, max_length=100, choices=[(3, 'ASTERISK'), (4, 'FREESWITCH'), (5, 'KAMAILIO'), (7, 'OPENSIPS'), (6, 'YATE')])),
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
