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
from django.conf.urls import patterns


urlpatterns = patterns('voip_billing.views',

                       (r'^rates/$', 'voip_rates'),
                       (r'^export_rate/$', 'export_rate'),
                       (r'^simulator/$', 'simulator'),
                       (r'^daily_billing_report/$', 'daily_billing_report'),
                       (r'^hourly_billing_report/$', 'hourly_billing_report'),
                       )
