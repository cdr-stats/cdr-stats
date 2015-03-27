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

from django.conf.urls import patterns

urlpatterns = patterns('cdr_alert.views',
                       # User detail change for Customer UI
                       (r'^alert/$', 'alarm_list'),
                       (r'^alert/add/$', 'alarm_add'),
                       (r'^alert/del/(.+)/$', 'alarm_del'),
                       (r'^alert/test/(.+)/$', 'alarm_test'),
                       (r'^alert/(.+)/$', 'alarm_change'),

                       (r'^trust_control/$', 'trust_control'),
                       (r'^alert_report/$', 'alert_report'),
                       )
