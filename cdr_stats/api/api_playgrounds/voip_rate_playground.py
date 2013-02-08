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
from django.utils.translation import gettext as _
from apiplayground import APIPlayground


class VoipRateAPIPlayground(APIPlayground):

    schema = {
        "title": _("Voip Rate API Playground"),
        "base_url": "http://localhost/api/v1/",
        "resources": [
            {
                "name": "/voip_rate/",
                "description": _("Resource to get voip rate."),
                "endpoints": [
                    {
                        "method": "GET",
                        "url": "/api/v1/voip_rate/",
                        "description": _("Returns all rates")
                    },
                    {
                        "method": "GET",
                        "url": "/api/v1/voip_rate/?dialcode={dialcode}",
                        "description": _("Returns a specific rate for prefix")
                    },
                    {
                        "method": "GET",
                        "url": "/api/v1/voip_rate/?recipient_phone_no={recipient-phone-no}",
                        "description": _("Returns a specific rate for recipient phone no")
                    },

                ]
            },
        ]
    }
