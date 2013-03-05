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


class SwitchAPIPlayground(APIPlayground):

    schema = {
        "title": _("switch"),
        "base_url": "http://localhost/api/v1/",
        "resources": [
            {
                "name": "/switch/",
                "description": _("resource to manage switches."),
                "endpoints": [
                    {
                        "method": "GET",
                        "url": "/api/v1/switch/",
                        "description": _("returns all switches")
                    },
                    {
                        "method": "GET",
                        "url": "/api/v1/switch/{switch-id}/",
                        "description": _("returns a specific switch")
                    },
                    {
                        "method": "POST",
                        "url": "/api/v1/switch/",
                        "description": _("creates new switch"),
                        "parameters": [
                            {
                                "name": "name",
                                "type": "string",
                                "is_required": True,
                                "default": "localhost"
                            },
                            {
                                "name": "ipaddress",
                                "type": "string",
                                "default": "192.168.1.4"
                            },
                        ]
                    },
                    {
                        "method": "PUT",
                        "url": "/api/v1/switch/{switch-id}/",
                        "description": _("update switch"),
                        "parameters": [
                            {
                                "name": "name",
                                "type": "string",
                                "is_required": True,
                                "default": "localhost"
                            },
                            {
                                "name": "ipaddress",
                                "type": "string",
                                "default": "192.168.1.4"
                            },
                        ]
                    },
                    {
                        "method": "DELETE",
                        "url": "/api/v1/switch/{switch-id}/",
                        "description": _("delete switch"),
                    }
                ]
            },
        ]
    }
