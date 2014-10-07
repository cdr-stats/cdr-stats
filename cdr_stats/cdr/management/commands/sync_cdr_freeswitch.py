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
from django.core.management.base import BaseCommand
from cdr.import_cdr_freeswitch_mongodb import import_cdr_freeswitch_mongodb, \
    apply_index
from optparse import make_option


class Command(BaseCommand):
    # Usage : sync_cdr
    help = "Sync Freeswitch with our CDR Record table\n" \
           "-------------------------------------------\n"\
           "Usage: python manage.py sync_cdr_freeswitch --apply-index\n"

    option_list = BaseCommand.option_list + (
        make_option('--apply-index',
            action='store_true',
            dest='apply-index',
            default=False,
            help=help),
    )

    def handle(self, *args, **options):

        for x in xrange(1, 10):
            import_cdr_freeswitch_mongodb(shell=True)

        # Apply index on collection
        if options['apply-index']:
            print "\nWe are going to apply index..."
            apply_index(shell=True)
