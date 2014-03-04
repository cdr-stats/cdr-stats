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

from django.conf import settings
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import Authorization
from tastypie.validation import Validation
from tastypie import fields
from user_profile.models import UserProfile
from cdr.import_cdr_freeswitch_mongodb import calculate_call_cost
from cdr.models import CDR_TYPE
from cdr.functions_def import get_hangupcause_id
from cdr_alert.functions_blacklist import chk_destination
from api.mongodb_resource import CDRMongoDBResource, Document
from uuid import uuid1
from datetime import datetime


class VoipCallValidation(Validation):
    """
    Voip Call Validation Class
    """

    def is_valid(self, bundle, request=None):
        errors = {}
        if not bundle.data:
            errors['Data'] = ['Data set is empty']

        voipplan_id = UserProfile.objects.get(user=request.user).voipplan_id
        if voipplan_id is None:
            errors['user_error'] = ["User is not attached with voip plan"]

        bundle.data['uuid'] = str(uuid1())
        bundle.data['date_start_uepoch'] = bundle.data.get('start_uepoch')

        if bundle.data.get('start_uepoch'):
            try:
                bundle.data['start_uepoch'] =  datetime.fromtimestamp(int(bundle.data.get('start_uepoch')[:10]))
            except:
                errors['start_uepoch_error'] = ["start_uepoch must be in timestamp format"]

        if bundle.data.get('answer_uepoch'):
            try:
                bundle.data['answer_uepoch'] =  datetime.fromtimestamp(int(bundle.data.get('answer_uepoch')[:10]))
            except:
                errors['answer_uepoch_error'] = ["answer_uepoch must be in timestamp format"]

        if bundle.data.get('end_uepoch'):
            try:
                bundle.data['end_uepoch'] =  datetime.fromtimestamp(int(bundle.data.get('end_uepoch')[:10]))
            except:
                errors['end_uepoch_error'] = ["end_uepoch must be in timestamp format"]

        destination_number = bundle.data.get('destination_number')
        if len(destination_number) <= settings.INTERNAL_CALL:
            bundle.data['authorized'] = 1
            bundle.data['country_id'] = 999
        else:
            destination_data = chk_destination(destination_number)
            bundle.data['authorized'] = destination_data['authorized']
            bundle.data['country_id'] = destination_data['country_id']

        try:
            bundle.data['hangup_cause_id'] = get_hangupcause_id(int(bundle.data.get('hangup_cause_id')))
        except:
            errors['hangup_cause_id_error'] = ["hangup_cause_id must be int"]

        try:
            # calculate billing of call
            billsec = bundle.data.get('billsec')
            call_rate = calculate_call_cost(voipplan_id, destination_number, billsec)
            bundle.data['buy_rate'] = call_rate['buy_rate']
            bundle.data['buy_cost'] = call_rate['buy_cost']
            bundle.data['sell_rate'] = call_rate['sell_rate']
            bundle.data['sell_cost'] = call_rate['sell_cost']
            bundle.data['cdr_type'] = CDR_TYPE['API']
        except:
            errors['billsec_error'] = ["billsec must be int"]

        return errors


class VoipCallResource(CDRMongoDBResource):
    """API to create voip cdr record and bill it

    **Attributes**:

        * ``switch_id`` -
        * ``caller_id_number`` -
        * ``caller_id_name`` -
        * ``destination_number`` -
        * ``duration`` -
        * ``billsec`` -
        * ``hangup_cause`` -
        * ``accountcode`` -
        * ``direction`` -
        * ``remote_media_ip`` -
        * ``start_uepoch`` -
        * ``answer_uepoch`` -
        * ``end_uepoch`` -
        * ``mduration`` -
        * ``billmsec`` -
        * ``read_codec`` -
        * ``write_codec`` -

    **Create**:

        CURL Usage::

            curl -u username:password --dump-header - -H "Content-Type:application/json" -X POST --data '{"accountcode":"1000", "answer_uepoch":"1359403221", "billmsec":"12960", "billsec":"104", "caller_id_name":"29914046", "caller_id_number":"29914046", "destination_number":"032287971777", "direction":"inbound", "duration":"154.0", "end_uepoch":"1359403221", "hangup_cause_id":"16", "mduration":"12960", "read_codec":"G711", "remote_media_ip":"192.168.1.21", "resource_uri":"", "start_uepoch":"1359403221", "switch_id":"1", "write_codec":"G711"}' http://localhost:8000/api/v1/voip_call/

        Response::

            HTTP/1.0 201 CREATED
            Date: Tue, 29 Jan 2013 11:31:13 GMT
            Server: WSGIServer/0.1 Python/2.7.3
            Vary: Accept-Language, Cookie
            Content-Type: text/html; charset=utf-8
            Location: http://localhost:8000/api/v1/voip_call/5107b3011d41c8168f076179/
            Content-Language: en-us

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
                        "read_codec":"G711",
                        "remote_media_ip":"192.168.1.21",
                        "sell_cost":"0.129",
                        "sell_rate":"0.0744",
                        "start_uepoch":"2013-01-05 23:12:09",
                        "switch_id":"1",
                        "uuid":"a993c388-5bc3-11e2-964f-000c2925d15f",
                        "write_codec":"G711"
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
    cdr_object_id = fields.CharField(attribute="cdr_object_id", null=True)

    class Meta:
        resource_name = "voip_call"
        list_allowed_methods = ["get", "post"]
        validation = VoipCallValidation()
        authorization = Authorization()
        authentication = BasicAuthentication()
        #object_class is a MongoDB Document
        object_class = Document
        collection = 'cdr_common'
