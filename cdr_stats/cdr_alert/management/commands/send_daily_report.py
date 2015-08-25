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
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from cdr.views import get_cdr_mail_report
from user_profile.models import UserProfile

import random

random.seed()


class Command(BaseCommand):
    help = "Send daily report, make sure to have an admin user with email and multiple_email.\n"

    def handle(self, *args, **options):
        """to send daily mail report via command line"""

        list_users = User.objects.filter(is_staff=True, is_active=True)
        for c_user in list_users:
            if not c_user.email:
                print "User (%s) -> This user doesn't have an email." % c_user.username
                continue
            else:
                print "Send Report from User (%s - %s)." % (c_user.username, c_user.email)

            try:
                to_email = UserProfile.objects.get(user=c_user).multiple_email
            except UserProfile.DoesNotExist:
                print 'Error: UserProfile not found (user_id:' + str(c_user.id) + ')'
                continue

            if not to_email:
                print 'Error: UserProfile multiple_email not set (user_id:' + str(c_user.id) + ')'
                continue

            from_email = c_user.email
            mail_data = get_cdr_mail_report(c_user)
            subject = 'CDR Report'

            html_content = get_template('cdr/mail_report_template.html')\
                .render(Context({
                    'yesterday_date': mail_data['yesterday_date'],
                    'rows': mail_data['rows'],
                    'total_duration': mail_data['total_duration'],
                    'total_calls': mail_data['total_calls'],
                    'total_buy_cost': mail_data['total_buy_cost'],
                    'total_sell_cost': mail_data['total_sell_cost'],
                    'metric_aggr': mail_data['metric_aggr'],
                    'country_data': mail_data['country_data'],
                    'hangup_cause_data': mail_data['hangup_cause_data']
                }))

            msg = EmailMultiAlternatives(subject, html_content, from_email, [to_email])
            print '\nEmail sent to ' + str(to_email)
            print '-' * 80
            msg.content_subtype = 'html'
            msg.send()
