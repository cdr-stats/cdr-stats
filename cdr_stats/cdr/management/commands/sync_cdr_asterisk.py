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
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe

from cdr.models import Switch, HangupCause, AsteriskCDR
from random import choice
from uuid import uuid1
from datetime import *
import calendar
import time
import sys
import random
import json, ast



class Command(BaseCommand):
    # Usage : sync_cdr_asterisk
    args = '<Switch ID>'
    help = "Sync Asterisk with our CDR Record table\n" \
           "-----------------------------------------\n\n" \
           "USAGE : python manage.py sync_cdr_asterisk <Server IP Address>\n"

    def handle(self, *args, **options):
        """Note that subscriber created this way are only for devel purposes"""

        if not args:
            print self.help
            raise SystemExit

        ipaddress = args[0]
        if not ipaddress or len(ipaddress)==0:
            print self.help
            raise SystemExit

        #Select the Switch ID
        try:
            switch = Switch.objects.get(ipaddress=ipaddress)
        except Switch.DoesNotExist:
            switch = Switch.object.create(name=ipaddress, ipaddress=ipaddress)

        if not switch.id:
            print "Error when adding new Switch!"
            raise SystemExit

        # Create Asterisk CDR record
        AsteriskCDR.objects.create(calldate=datetime.datetime.now(),
                                   src='xxxx',
                                   dst='xxxx',
                                   clid='xxxx',
                                   dcontext='xxxx',
                                   channel='xxxx',
                                   dstchannel='xxxx',
                                   lastapp=request.user,
                                   lastdata=request.user,
                                   duration=0,
                                   billsec=0,
                                   disposition=1,
                                   amaflags='xxxx',
                                   accountcode='xxxx',
                                   uniqueid='xxxx',
                                   userfield='xxxx',
                                   cost='xxxx',
                                   vendor='xxxx',
                                   switch_id=switch.id
                                   )
