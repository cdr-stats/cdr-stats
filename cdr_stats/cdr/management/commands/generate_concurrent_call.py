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
from cdr.aggregate import set_concurrentcall_analytic
from random import choice
from optparse import make_option
import random
import datetime
from mongodb_connection import mongodb


random.seed()

HANGUP_CAUSE = ['NORMAL_CLEARING', 'NORMAL_CLEARING', 'NORMAL_CLEARING',
                'NORMAL_CLEARING', 'USER_BUSY', 'NO_ANSWER', 'CALL_REJECTED',
                'INVALID_NUMBER_FORMAT']


class Command(BaseCommand):
    help = "Generate random Concurrent calls\n"\
           "---------------------------------\n"\
           "python manage.py generate_concurrent_call --delta-day=0\n"\
           "python manage.py generate_concurrent_call -d 0"

    option_list = BaseCommand.option_list + (
        make_option('--delta-day', '-d',
            default=None,
            dest='delta-day',
            help=help),
    )

    def handle(self, *args, **options):
        """Note that subscriber created this way are only for devel purposes"""
        if not mongodb.conc_call:
            print "Error mongodb Connection"

        no_of_record = 86400  # second in one day

        if options.get('delta-day'):
            try:
                day_delta_int = int(options.get('delta-day'))
            except ValueError:
                day_delta_int = 1
        else:
            day_delta_int = 1

        accountcode = ''.join([choice('1234567890') for i in range(4)])
        accountcode = '12345'
        now = datetime.datetime.today()
        date_now = datetime.datetime(now.year, now.month, now.day, now.hour,
                                     now.minute, now.second, 0)

        today_delta = datetime.timedelta(hours=datetime.datetime.now().hour,
                minutes=datetime.datetime.now().minute,
                seconds=datetime.datetime.now().second)
        date_today = date_now - today_delta \
            - datetime.timedelta(days=day_delta_int)

        numbercall = 10

        for i in range(0, int(no_of_record)):
            delta_duration = i
            call_date = date_today + datetime.timedelta(seconds=delta_duration)

            delta_call = random.randint(-2, 2)
            numbercall = numbercall + delta_call
            switch_id = 1

            if numbercall < 0:
                numbercall = 0
            print '%s (accountcode:%s, switch_id:%d) ==> %d' % (call_date,
                    accountcode, switch_id, numbercall)

            call_json = {'switch_id': switch_id, 'call_date': call_date,
                         'numbercall': numbercall, 'accountcode': accountcode}

            mongodb.conc_call.insert(call_json)

            #Create collection for Analytics
            set_concurrentcall_analytic(call_date, switch_id, accountcode, numbercall)
