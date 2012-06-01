# -*- coding: utf-8 -*-

#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2012 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#
from django.core.management.base import BaseCommand
from cdr.import_cdr_asterisk_mysql import import_cdr_asterisk_mysql


class Command(BaseCommand):
    """
    Command line to import Asterisk CDR with Mysql
    """
    help = \
        '''
Sync Asterisk with our CDR Record table
-----------------------------------------
USAGE : python manage.py sync_cdr_asterisk
'''

    def handle(self, *args, **options):

        import_cdr_asterisk_mysql(shell=True)
