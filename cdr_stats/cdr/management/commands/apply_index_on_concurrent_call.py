# -*- coding: utf-8 -*-

#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2013 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#
from django.core.management.base import BaseCommand
from django.conf import settings

CONC_CALL_AGG = settings.DBCON[settings.MONGO_CDRSTATS['CONC_CALL_AGG']]

class Command(BaseCommand):
    #args = ''
    help = "Apply index on concurrent call collection\n"\
           "-----------------------------------------\n"\
           "python manage.py apply_index_on_concurrent_call"    

    def handle(self, *args, **options):
        """
        Note that rates created this way are only for devel purposes
        """
        CONC_CALL_AGG.ensure_index([('call_date', -1), ('switch_id', 1), ('accountcode', 1)],
                               unique=True)
        
        print "Index applied on concurrnt calls"
