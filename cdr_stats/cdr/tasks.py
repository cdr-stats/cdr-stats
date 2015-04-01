# -*- coding: utf-8 -*-
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

from django.db import connection
from celery.task import PeriodicTask
from cdr.cdr_importer import import_cdr
from django_lets_go.only_one_task import only_one
from datetime import timedelta

# Note: if you import a lot of CDRs the first time you can have an issue here
# we need to make sure the user import their CDR before starting Celery
# for now we will increase the lock limit to 1 hours
LOCK_EXPIRE = 60 * 60 * 1  # Lock expires in 1 hours


class run_cdr_import(PeriodicTask):
    """
    A periodic task that checks for new CDRs to import
    """
    run_every = timedelta(seconds=15)

    @only_one(ikey="run_cdr_import", timeout=LOCK_EXPIRE)
    def run(self, **kwargs):
        logger = self.get_logger()
        logger.info('TASK :: run_cdr_import')

        # launch the CDRs import
        import_cdr()

        return True


class refresh_materialized_views(PeriodicTask):
    """
    A periodic task that refresh the materialized views
    """
    run_every = timedelta(minutes=15)

    def run(self, **kwargs):
        logger = self.get_logger()
        logger.info('TASK :: refresh_materialized_views')

        # Refresh matv_voip_cdr_aggr_hour
        with connection.cursor() as cursor:
            cursor.execute("REFRESH MATERIALIZED VIEW matv_voip_cdr_aggr_hour;")

        # Refresh matv_voip_cdr_aggr_min
        with connection.cursor() as cursor:
            cursor.execute("REFRESH MATERIALIZED VIEW matv_voip_cdr_aggr_min;")

        return True
