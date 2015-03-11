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


urlpatterns = patterns('realtime.views',
                       (r'^concurrent_calls/$', 'cdr_concurrent_calls'),
                       (r'^realtime/$', 'cdr_realtime'),
                       # (r'^get_realtime_json/$', 'cdr.ajax.get_realtime_json'),
                       )
