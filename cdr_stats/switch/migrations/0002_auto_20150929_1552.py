# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('switch', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='switch',
            name='switch_type',
            field=models.IntegerField(default=3, max_length=100, choices=[(4, 'ASTERISK'), (3, 'FREESWITCH'), (6, 'KAMAILIO'), (7, 'OPENSIPS'), (8, 'SIPWISE'), (0, 'UNKNOWN'), (9, 'VERAZ'), (5, 'YATE')]),
            preserve_default=True,
        ),
    ]
