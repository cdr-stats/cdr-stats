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


class CdrAPIPlayground(APIPlayground):
    """
    To test CDR api in browse

        ``URL`` : http://127.0.0.1:8000/api-explorer/cdr/
    """

    schema = {
        "title": "CDR API Playground",
        "base_url": "http://localhost/api/v1/",
        "resources": [
            {
                "name": "/cdr/",
                "description": "This resource allows you to manage cdr.",
                "endpoints": [
                    {
                        "method": "POST",
                        "url": "/api/v1/cdr/",
                        "description": "Creates new phonebook",
                        "parameters": [
                            {
                                "name": "switch_id",
                                "type": "string",
                                "is_required": True,
                                "default": "1"
                            },
                            {
                                "name": "caller_id_number",
                                "type": "string",
                                "default": "12345"
                            },
                            {
                                "name": "caller_id_name",
                                "type": "string",
                                "default": "xyz"
                            },
                            {
                                "name": "destination_number",
                                "type": "string",
                                "default": "9972374874"
                            },
                            {
                                "name": "duration",
                                "type": "string",
                                "default": "12"
                            },
                            {
                                "name": "billsec",
                                "type": "string",
                                "default": "15"
                            },
                            {
                                "name": "hangup_cause_q850",
                                "type": "string",
                                "default": "16"
                            },
                            {
                                "name": "accountcode",
                                "type": "string",
                                "default": "32523"
                            },
                            {
                                "name": "direction",
                                "type": "string",
                                "default": "IN"
                            },
                            {
                                "name": "uuid",
                                "type": "string",
                                "default": "e8fee8f6-40dd-11e1-964f-000c296bd875"
                            },
                            {
                                "name": "remote_media_ip",
                                "type": "string",
                                "default": "127.0.0.1"
                            },
                            {
                                "name": "start_uepoch",
                                "type": "string",
                                "default": "2012-02-20 12:23:34"
                            },
                            {
                                "name": "answer_uepoch",
                                "type": "string",
                                "default": "2012-02-20 12:23:34"
                            },
                            {
                                "name": "end_uepoch",
                                "type": "string",
                                "default": "2012-02-20 12:23:34"
                            },
                            {
                                "name": "mduration",
                                "type": "string",
                                "default": "32"
                            },
                            {
                                "name": "billmsec",
                                "type": "string",
                                "default": "43"
                            },
                            {
                                "name": "read_codec",
                                "type": "string",
                                "default": "xyz"
                            },
                            {
                                "name": "write_codec",
                                "type": "string",
                                "default": "abc"
                            },
                            {
                                "name": "cdr_type",
                                "type": "string",
                                "default": "1"
                            },
                        ]
                    },
                ]
            },
        ]
    }
