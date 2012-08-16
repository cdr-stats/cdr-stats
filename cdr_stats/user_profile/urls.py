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

from django.conf.urls import patterns, include


urlpatterns = patterns('',
    # User detail change for Customer UI
    (r'^user_detail_change/$', 'user_profile.views.customer_detail_change'),

    (r'^user_detail_change/', include('notification.urls')),
    (r'^user_detail_change/del/(.+)/$',
                                'user_profile.views.notification_del_read'),

    # Notification Status (seen/unseen) for customer UI
    (r'^update_notice_status_cust/(\d*)/$',
                    'user_profile.views.update_notice_status_cust'),
)
