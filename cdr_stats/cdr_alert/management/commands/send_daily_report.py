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
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from cdr.views import get_cdr_mail_report
from user_profile.models import UserProfile

import random

random.seed()


class Command(BaseCommand):
    help = "Send daily report\n"\
           "---------------------------------\n"\
           "python manage.py send_daily_report\n"\


    def handle(self, *args, **options):
        """to send daily mail report via command line"""

        list_users = User.objects.filter(is_staff=True, is_active=True)
        for c_user in list_users:
            if not c_user.email:
                print "User (%s) -> This user doesn't have an email." % c_user.username
                continue
            from_email = c_user.email
            try:
                to = UserProfile.objects.get(user=c_user).multiple_email
            except UserProfile.DoesNotExist:
                print 'Error: UserProfile not found (user_id:' + str(c_user.id) + ')'
                continue

            mail_data = get_cdr_mail_report()

            subject = _('CDR Report')

            html_content = get_template('cdr/mail_report_template.html')\
                .render(Context({
                    'yesterday_date': mail_data['yesterday_date'],
                    'rows': mail_data['rows'],
                    'total_duration': mail_data['total_duration'],
                    'total_calls': mail_data['total_calls'],
                    'ACT': mail_data['ACT'],
                    'ACD': mail_data['ACD'],
                    'country_analytic_array': mail_data['country_analytic_array'],
                    'hangup_analytic_array': mail_data['hangup_analytic_array']
                }))

            if to:
                msg = EmailMultiAlternatives(subject, html_content, from_email, [to])
                print '\nEmail sent to ' + str(to)
                print '-' * 80
                msg.content_subtype = 'html'
                msg.send()
            else:
                print "Error: email not sent"
