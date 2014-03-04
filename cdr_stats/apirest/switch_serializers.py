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
from rest_framework import serializers
from cdr.models import Switch


class SwitchSerializer(serializers.HyperlinkedModelSerializer):
    """
    **Read**:

        CURL Usage::

            curl -u username:password -H 'Accept: application/json' http://localhost:8000/rest-api/switch/

            curl -u username:password -H 'Accept: application/json' http://localhost:8000/rest-api/switch/%switch-id%/

        Response::

            {
                "count": 1,
                "next": null,
                "previous": null,
                "results": [
                    {
                        "url": "http://127.0.0.1:8000/rest-api/switch/1/", 
                        "name": "localhost", 
                        "ipaddress": "127.0.0.1", 
                        "key_uuid": "25116b72-b477-11e1-964f-000c296bd875"
                    }
                ]
            }
    """
    class Meta:
        model = Switch
