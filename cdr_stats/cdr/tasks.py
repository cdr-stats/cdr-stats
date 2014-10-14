# -*- coding: utf-8 -*-
#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2014 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from django.conf import settings
from celery.task import PeriodicTask
from cdr.import_cdr_freeswitch_mongodb import import_cdr_freeswitch_mongodb
from cdr.import_cdr_asterisk import import_cdr_asterisk
from django_lets_go.only_one_task import only_one
from datetime import timedelta

#Note: if you import a lot of CDRs the first time you can have an issue here
#we need to make sure the user import their CDR before starting Celery
#for now we will increase the lock limit to 1 hours
LOCK_EXPIRE = 60 * 60 * 1  # Lock expires in 1 hours


class sync_cdr_pending(PeriodicTask):
    """
    A periodic task that checks for pending CDR to import
    """
    run_every = timedelta(seconds=10)  # every 10 secs

    @only_one(ikey="sync_cdr_pending", timeout=LOCK_EXPIRE)
    def run(self, **kwargs):
        logger = self.get_logger()
        logger.info('TASK :: sync_cdr_pending')

        if settings.CDR_BACKEND[settings.LOCAL_SWITCH_IP]['cdr_type'] == 'asterisk':
            # Import from Asterisk
            import_cdr_asterisk()

        elif settings.CDR_BACKEND[settings.LOCAL_SWITCH_IP]['cdr_type'] == 'freeswitch':
            # Import from Freeswitch Mongo
            import_cdr_freeswitch_mongodb()

        return True
