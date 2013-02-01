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
from django.utils.translation import gettext as _
from apiplayground import APIPlayground
from datetime import datetime, timedelta
import time


class VoipCallAPIPlayground(APIPlayground):
    """
    To test CDR api in broswer

        ``URL`` : http://127.0.0.1:8000/api-explorer/voip-call/
    """
    # convert s_uepoch/e_uepoch into milliseconds
    s_uepoch = datetime.now()
    start_uepoch = int(time.mktime(s_uepoch.timetuple()))
    e_uepoch = s_uepoch + timedelta(seconds=100)
    end_uepoch = int(time.mktime(e_uepoch.timetuple()))

    schema = {
        "title": _("To record CDRs and bill them"),
        "base_url": "http://localhost/api/v1/",
        "resources": [
            {
                "name": "/voip_call/",
                "description": _("This resource allows to record CDRs and bill them."),
                "endpoints": [
                    {
                        "method": "GET",
                        "url": "/api/v1/voip_call/",
                        "description": _("Returns all CDRs")
                    },
                    {
                        "method": "GET",
                        "url": "/api/v1/voip_call/{id}/",
                        "description": _("Returns a specific cdr")
                    },
                    {
                        "method": "POST",
                        "url": "/api/v1/voip_call/",
                        "description": _("Creates new billed voip call"),
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
                                "default": "48092924"
                            },
                            {
                                "name": "caller_id_name",
                                "type": "string",
                                "default": "CallerName"
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
                                "default": "90"
                            },
                            {
                                "name": "hangup_cause_id",
                                "type": "string",
                                "default": "16"
                            },
                            {
                                "name": "direction",
                                "type": "string",
                                "default": "INBOUND"
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
                                "default": start_uepoch
                            },
                            {
                                "name": "answer_uepoch",
                                "type": "string",
                                "default": start_uepoch
                            },
                            {
                                "name": "end_uepoch",
                                "type": "string",
                                "default": end_uepoch
                            },
                            {
                                "name": "mduration",
                                "type": "string",
                                "default": "10000"
                            },
                            {
                                "name": "billmsec",
                                "type": "string",
                                "default": "90000"
                            },
                            {
                                "name": "read_codec",
                                "type": "string",
                                "default": "G711"
                            },
                            {
                                "name": "write_codec",
                                "type": "string",
                                "default": "G711"
                            },
                        ]
                    },
                ]
            },
        ]
    }
