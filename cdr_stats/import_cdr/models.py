#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2015 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from __future__ import unicode_literals

from django.db import models
from postgres.fields import json_field


class CDRImport(models.Model):
    """
    CDRImport table live on Database 'import_cdr'

    Manually selecting a database for a QuerySet:
    CDRImport.objects.using('import_cdr').all()
    """
    id = models.AutoField(primary_key=True)
    switch = models.CharField(max_length=80)
    cdr_source_type = models.IntegerField(blank=True, null=True)
    callid = models.CharField(max_length=80)
    caller_id_number = models.CharField(max_length=80)
    caller_id_name = models.CharField(max_length=80)
    destination_number = models.CharField(max_length=80)
    dialcode = models.CharField(max_length=10, blank=True)
    state = models.CharField(max_length=5, blank=True)
    channel = models.CharField(max_length=80, blank=True)
    starting_date = models.DateTimeField()
    duration = models.IntegerField()
    billsec = models.IntegerField()
    progresssec = models.IntegerField(blank=True, null=True)
    answersec = models.IntegerField(blank=True, null=True)
    waitsec = models.IntegerField(blank=True, null=True)
    hangup_cause_id = models.IntegerField(blank=True, null=True)
    hangup_cause = models.CharField(max_length=80, blank=True)
    direction = models.IntegerField(blank=True, null=True)
    country_code = models.CharField(max_length=3, blank=True)
    accountcode = models.CharField(max_length=40, blank=True)
    buy_rate = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)
    buy_cost = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    sell_rate = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)
    sell_cost = models.DecimalField(max_digits=12, decimal_places=5, blank=True, null=True)
    imported = models.BooleanField(default=False)

    # Postgresql >= 9.4 Json field
    extradata = json_field.JSONField(blank=True)

    def __unicode__(self):
        return '[%s] %s - dur:%d - hangup:%d' % \
            (self.id, self.destination_number, self.duration, self.hangup_cause_id)

    class Meta:
        # Remove `managed = False` lines if you wish to allow Django to create, modify,
        # and delete the table
        # managed = False
        verbose_name = "CDR Import"
        verbose_name_plural = "CDRs Import"
        db_table = 'cdr_import'
