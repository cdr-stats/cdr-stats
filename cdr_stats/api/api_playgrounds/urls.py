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
from api.api_playgrounds.switch_playground import SwitchAPIPlayground
from api.api_playgrounds.voip_rate_playground import VoipRateAPIPlayground
from api.api_playgrounds.voip_call_playground import VoipCallAPIPlayground


urlpatterns = patterns('',
    (r'api-explorer/cdr/', include(CdrAPIPlayground().urls)),
    (r'api-explorer/switch/', include(SwitchAPIPlayground().urls)),
    (r'api-explorer/voip-rate/', include(VoipRateAPIPlayground().urls)),
    (r'api-explorer/voip-call/', include(VoipCallAPIPlayground().urls)),

    # API list view
    (r'api-explorer/$', 'api.api_playgrounds.views.api_list_view'),
)
