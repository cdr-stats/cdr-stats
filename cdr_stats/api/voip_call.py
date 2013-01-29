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

from django.conf import settings
from tastypie.resources import ModelResource
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import Authorization
from tastypie.validation import Validation
from tastypie.throttle import BaseThrottle
from tastypie import fields

from user_profile.models import UserProfile
from datetime import datetime
from api.mongodb_resource import MongoDBResource, Document


class VoipCallResource(MongoDBResource):
    """API to create voip cdr record and bill it

    **Attributes**:

        * ``recipient_phone_no`` -
        * ``sender_phone_no`` -
        * ``disposition`` -
        * ``call_date`` -


    **Create**:

         CURL Usage::

             curl -u username:password --dump-header - -H "Content-Type:application/json" -X POST --data '{"recipient_phone_no": "34657077888", "sender_phone_no": "919427164510", "disposition": "1", "call_date": "2013-01-11 11:11:22"}' http://localhost:8000/api/v1/voip_call_billed/

         Response::

            

    **Read**:

         CURL Usage::

             curl -u username:password -H 'Accept: application/json' -X GET http://localhost:8000/api/v1/voip_call/?format=json

             curl -u username:password -H 'Accept: application/json' -X GET http://localhost:8000/api/v1/voip_call/%_id%/?format=json

         Response::

            {
               "meta":{
                  "limit":20,
                  "next":"/api/v1/voip_call/?offset=20&limit=20&format=json",
                  "offset":0,
                  "previous":null,
                  "total_count":161
               },
               "objects":[
                  {
                     "accountcode":"1000",
                     "answer_uepoch":"2012-01-26 01:35:53",
                     "authorized":"True",
                     "billmsec":"12960",
                     "billsec":"104",
                     "buy_cost":"0.1075",
                     "buy_rate":"0.062",
                     "caller_id_name":"29914046",
                     "caller_id_number":"29914046",
                     "cdr_object_id":"50efc46d1d41c81733b6939d",
                     "cdr_type":"1",
                     "country_id":"21",
                     "destination_number":"032287971777",
                     "direction":"inbound",
                     "duration":"154.0",
                     "end_uepoch":"2012-01-26 01:36:06",
                     "hangup_cause_id":"8",
                     "id":"50efc47b1d41c8174542f4d6",
                     "mduration":"12960",
                     "read_codec":"G722",
                     "remote_media_ip":"192.168.1.21",
                     "resource_uri":"",
                     "sell_cost":"0.129",
                     "sell_rate":"0.0744",
                     "start_uepoch":"2013-01-05 23:12:09",
                     "switch_id":"1",
                     "uuid":"a993c388-5bc3-11e2-964f-000c2925d15f",
                     "write_codec":"G722"
                  }                  
               ]
            }
    """
    id = fields.CharField(attribute="_id")
    switch_id = fields.CharField(attribute="switch_id")
    caller_id_number = fields.CharField(attribute="caller_id_number")
    caller_id_name = fields.CharField(attribute="caller_id_name")
    destination_number = fields.CharField(attribute="destination_number")
    duration = fields.CharField(attribute="duration")
    billsec = fields.CharField(attribute="billsec")
    hangup_cause_id = fields.CharField(attribute="hangup_cause_id")
    accountcode = fields.CharField(attribute="accountcode")
    direction = fields.CharField(attribute="direction")
    uuid = fields.CharField(attribute="uuid")
    remote_media_ip = fields.CharField(attribute="remote_media_ip")
    start_uepoch = fields.CharField(attribute="start_uepoch")
    answer_uepoch = fields.CharField(attribute="answer_uepoch")
    end_uepoch = fields.CharField(attribute="end_uepoch")
    mduration = fields.CharField(attribute="mduration")
    billmsec = fields.CharField(attribute="billmsec")

    read_codec = fields.CharField(attribute="read_codec")
    write_codec = fields.CharField(attribute="write_codec")
    cdr_type = fields.CharField(attribute="cdr_type")
    cdr_object_id = fields.CharField(attribute="cdr_object_id")
    country_id = fields.CharField(attribute="country_id")
    authorized = fields.CharField(attribute="authorized")
    buy_rate = fields.CharField(attribute="buy_rate")
    buy_cost = fields.CharField(attribute="buy_cost")
    sell_rate = fields.CharField(attribute="sell_rate")
    sell_cost = fields.CharField(attribute="sell_cost")
    #billmsec = fields.CharField(attribute="billmsec")

    class Meta:
        resource_name = "voip_call"
        list_allowed_methods = ["delete", "get", "post"]
        authorization = Authorization()
        object_class = Document
        collection = 'cdr_common' # collection name
