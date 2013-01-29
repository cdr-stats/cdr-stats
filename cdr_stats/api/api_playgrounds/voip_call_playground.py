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
from datetime import datetime


class VoipCallAPIPlayground(APIPlayground):
    """
    To test CDR api in broswer

        ``URL`` : http://127.0.0.1:8000/api-explorer/voip-call/
    """         
    schema = {
        "title": "Voip call billed API Playground",
        "base_url": "http://localhost/api/v1/",
        "resources": [
            {
                "name": "/voip_call_billed/",
                "description": "This resource allows you to bill voip call.",
                "endpoints": [
                    {
                        "method": "GET",
                        "url": "/api/v1/voip_call/",
                        "description": "Returns all CDRs"
                    },
                    {
                        "method": "GET",
                        "url": "/api/v1/voip_call/{id}/",
                        "description": "Returns a specific cdr"
                    },
                    {
                        "method": "POST",
                        "url": "/api/v1/voip_call/",
                        "description": "Creates new billed voip call",
                        "parameters": [{
                                           "name": "switch_id",
                                           "type": "string",
                                           "is_required": True,
                                           "default": "1"
                                       },
                                       {
                                           "name": "caller_id_number",
                                           "type": "string",
                                           "default": "48092924"
                                       },
                                       {
                                           "name": "caller_id_name",
                                           "type": "string",
                                           "default": "Areski"
                                       },
                                       {
                                           "name": "destination_number",
                                           "type": "string",
                                           "default": "3465778800"
                                       },
                                       {
                                           "name": "duration",
                                           "type": "string",
                                           "is_required": True,
                                           "default": "100"
                                       },
                                       {
                                           "name": "billsec",
                                           "type": "string",
                                           "default": "50"
                                       },
                                       {
                                           "name": "hangup_cause_id",
                                           "type": "string",
                                           "default": "1"
                                       },
                                       {
                                           "name": "direction",
                                           "type": "string",
                                           "default": "INBOUND"
                                       },
                                       {
                                           "name": "uuid",
                                           "type": "string",
                                           "default": ""
                                       },
                                       {
                                           "name": "remote_media_ip",
                                           "type": "string",
                                           "default": "127.0.0.1"
                                       },
                                       {
                                           "name": "accountcode",
                                           "type": "string",
                                           "default": "123456"
                                       },
                                       {
                                           "name": "start_uepoch",
                                           "type": "string",
                                           "default": datetime.today().strftime('%Y-%m-%d %H:%M:%S')
                                       },
                                       {
                                           "name": "answer_uepoch",
                                           "type": "string",
                                           "default": datetime.today().strftime('%Y-%m-%d %H:%M:%S')
                                       },
                                       {
                                           "name": "end_uepoch",
                                           "type": "string",
                                           "default": datetime.today().strftime('%Y-%m-%d %H:%M:%S')
                                       },
                                       {
                                           "name": "mduration",
                                           "type": "string",
                                           "default": "12"
                                       },
                                       {
                                           "name": "billmsec",
                                           "type": "string",
                                           "default": "25"
                                       },
                                       {
                                           "name": "read_codec",
                                           "type": "string",
                                           "default": "G727"
                                       },
                                       {
                                           "name": "write_codec",
                                           "type": "string",
                                           "default": "G727"
                                       },
                                       {
                                           "name": "cdr_type",
                                           "type": "string",
                                           "default": ""
                                       },
                                       {
                                           "name": "cdr_object_id",
                                           "type": "string",
                                           "default": ""
                                       },
                                       {
                                           "name": "country_id",
                                           "type": "string",
                                           "default": "1"
                                       },
                                       {
                                           "name": "authorized",
                                           "type": "string",
                                           "default": "TRUE"
                                       },
                                       ]
                    },
                    ]
            },
            ]
    }
