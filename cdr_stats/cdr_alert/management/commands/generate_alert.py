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
from cdr_alert.models import Alarm, AlarmReport
from optparse import make_option
import random
import datetime


random.seed()


class Command(BaseCommand):
    help = "Generate alert\n"\
           "---------------------------------\n"\
           "python manage.py generate_alert --alert-no=10 --delta-day=0\n"\
           "python manage.py generate_alert -a 10 -d 0"

    option_list = BaseCommand.option_list + (
        make_option('--delta-day', '-d',
            default=None,
            dest='delta-day',
            help=help),
        make_option('--alert-no', '-a',
            default=None,
            dest='alert-no',
            help=help),
    )

    def handle(self, *args, **options):
        """
        Note that alert created this way are only for devel purposes
        """
        day_delta_int = 7  # default
        if options.get('delta-day'):
            try:
                day_delta_int = int(options.get('delta-day'))
            except ValueError:
                day_delta_int = 7
        else:
            day_delta_int = 7

        if options.get('alert-no'):
            try:
                alert_no = int(options.get('alert-no'))
            except ValueError:
                alert_no = 1
        else:
            alert_no = 1

        alarm_count = Alarm.objects.all().count()
        if alarm_count == 0:
            alarm = Alarm.objects.create(user_id=1,
                                         name='test_alert',
                                         alert_value=10,
                                         email_to_send_alarm='admin@localhost.com')

        # To get random alarm object
        alarm = Alarm.objects.order_by('?')[:1]

        calculatedvalue = 10

        for i in range(0, int(alert_no)):
            delta_days = random.randint(0, day_delta_int)
            delta_minutes = random.randint(1, 1440)
            daterun = datetime.datetime.now()\
                - datetime.timedelta(minutes=delta_minutes)\
                - datetime.timedelta(days=delta_days)

            delta_call = random.randint(-2, 2)
            calculatedvalue = calculatedvalue + delta_call

            AlarmReport.objects.create(
                alarm=alarm[0],
                calculatedvalue=calculatedvalue,
                status=random.randint(1, 2),
                daterun=daterun)
            print "alarm_report -> alarm:%s, daterun=%s, calculatedvalue=%d" % \
                (alarm[0], daterun, calculatedvalue)

        print "\nDone"
