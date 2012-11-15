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
from apiplayground import APIPlayground


class SwitchAPIPlayground(APIPlayground):

    schema = {
        "title": "Switch API Playground",
        "base_url": "http://localhost/api/v1/",
        "resources": [
            {
                "name": "/switch/",
                "description": "This resource allows you to manage switchs.",
                "endpoints": [
                    {
                        "method": "GET",
                        "url": "/api/v1/switch/",
                        "description": "Returns all switchs"
                    },
                    {
                        "method": "GET",
                        "url": "/api/v1/switch/{switch-id}/",
                        "description": "Returns a specific switch"
                    },
                    {
                        "method": "POST",
                        "url": "/api/v1/switch/",
                        "description": "Creates new switch",
                        "parameters": [{
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
                        "description": "Update switch",
                        "parameters": [{
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
                        "description": "Delete switch",
                        }
                ]
            },
            ]
    }
