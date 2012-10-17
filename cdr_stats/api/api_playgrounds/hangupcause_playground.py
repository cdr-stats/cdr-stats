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


class HangupcauseAPIPlayground(APIPlayground):

    schema = {
        "title": "Hangup Cause API Playground",
        "base_url": "http://localhost/api/v1/",
        "resources": [
            {
                "name": "/hangup_cause/",
                "description": "This resource allows you to manage hangup cause.",
                "endpoints": [
                    {
                        "method": "GET",
                        "url": "/api/v1/hangup_cause/",
                        "description": "Returns all sections"
                    },
                    {
                        "method": "GET",
                        "url": "/api/v1/hangup_cause/{hangup-cause-id}/",
                        "description": "Returns a specific hangup cause"
                    },
                    {
                        "method": "POST",
                        "url": "/api/v1/hangup_cause/",
                        "description": "Creates new hangup cause",
                        "parameters": [{
                                           "name": "code",
                                           "type": "string",
                                           "is_required": True,
                                           "default": "0"
                                       },
                                       {
                                           "name": "enumeration",
                                           "type": "string",
                                           "default": "UNSPECIFIED"
                                       },
                                       {
                                           "name": "cause",
                                           "type": "string",
                                           "default": "Unspecified. No other cause codes applicable."
                                       },
                                       {
                                           "name": "description",
                                           "type": "string",
                                           "default": "This is usually given by the router when none of the other codes apply. This cause usually occurs in the same type of situations as cause 1, cause 88, and cause 100. "
                                       },
                                       ]
                    },
                    {
                        "method": "PUT",
                        "url": "/api/v1/hangup_cause/{hangup-cause-id}/",
                        "description": "Update hangup cause",
                        "parameters": [{
                                           "name": "code",
                                           "type": "string",
                                           "is_required": True,
                                           "default": "0"
                                       },
                                       {
                                           "name": "enumeration",
                                           "type": "string",
                                           "default": "UNSPECIFIED"
                                       },
                                       {
                                           "name": "cause",
                                           "type": "string",
                                           "default": "Unspecified. No other cause codes applicable."
                                       },
                                       {
                                           "name": "description",
                                           "type": "string",
                                           "default": "This is usually given by the router when none of the other codes apply. This cause usually occurs in the same type of situations as cause 1, cause 88, and cause 100. "
                                       },
                                       ]
                    },
                    {
                        "method": "DELETE",
                        "url": "/api/v1/hangup_cause/{hangup-cause-id}/",
                        "description": "Delete hangup cause",
                        }
                ]
            },
            ]
    }