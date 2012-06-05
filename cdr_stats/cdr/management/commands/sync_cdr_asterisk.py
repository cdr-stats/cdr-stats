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
from cdr.import_cdr_freeswitch_mongodb import apply_index


class Command(BaseCommand):
    """
    Command line to import Asterisk CDR with Mysql
    """
    args = ' apply_index '
    help = \
        '''
Sync Asterisk with our CDR Record table
-----------------------------------------
USAGE : python manage.py sync_cdr_asterisk 1
        python manage.py sync_cdr_asterisk 0
'''

    def handle(self, *args, **options):

        if not args or len(args) != 1:
            print self.help
            # print >> sys.stderr
            raise SystemExit

        apply_index_var = args[0]
        try:
            apply_index_var = int(apply_index_var)
        except ValueError:
            apply_index_var = 0

        import_cdr_asterisk_mysql(shell=True)

        # Apply index on collection
        if apply_index_var == 1:
            apply_index(shell=True)
