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
from django.conf.urls import include, patterns
from api.api_playgrounds.cdr_playground import CdrAPIPlayground
from api.api_playgrounds.hangupcause_playground import HangupcauseAPIPlayground


urlpatterns = patterns('',

    (r'explorer/cdr/', include(CdrAPIPlayground().urls)),
    (r'explorer/hangupcause/', include(HangupcauseAPIPlayground().urls)),

    # API list view
    (r'explorer/$', 'api.api_playgrounds.views.api_list_view'),
)
