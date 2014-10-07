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


urlpatterns = patterns('mod_registration.views',
    # Password reset for Customer UI
    (r'^password_reset/$', 'cust_password_reset'),
    (r'^password_reset/done/$', 'cust_password_reset_done'),
    (r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
        'cust_password_reset_confirm'),
    (r'^reset/done/$', 'cust_password_reset_complete'),
)
