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
from cdr.cdr_importer import import_cdr


class Command(BaseCommand):

    """
    Command line to import CDR with CDR data store
    """
    help = "Import new CDRs\n"\
           "---------------\n"\
           "USAGE : python manage.py import_cdr\n"

    option_list = BaseCommand.option_list

    def handle(self, *args, **options):

        import_cdr(shell=True)
