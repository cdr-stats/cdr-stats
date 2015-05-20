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
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):

    """
    Command line to import CDR with CDR data store
    """
    help = "Refresh Materialized View\n"\
           "-------------------------\n"\
           "USAGE : python manage.py refresh_mat_view\n"

    option_list = BaseCommand.option_list

    def handle(self, *args, **options):

        # Refresh matv_voip_cdr_aggr_hour
        with connection.cursor() as cursor:
            print("REFRESH MATERIALIZED VIEW matv_voip_cdr_aggr_hour;")
            cursor.execute("REFRESH MATERIALIZED VIEW matv_voip_cdr_aggr_hour;")

        # Refresh matv_voip_cdr_aggr_min
        with connection.cursor() as cursor:
            print("REFRESH MATERIALIZED VIEW matv_voip_cdr_aggr_min;")
            cursor.execute("REFRESH MATERIALIZED VIEW matv_voip_cdr_aggr_min;")
