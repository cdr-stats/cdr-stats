# -*- coding: utf-8 -*-

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
import logging
from datetime import datetime

from django.conf.urls.defaults import url
from django.http import HttpResponse, HttpResponseNotFound
from django.conf import settings

from tastypie.resources import ModelResource
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import Authorization
from tastypie.throttle import BaseThrottle
from tastypie.exceptions import ImmediateHttpResponse
from tastypie import http

from cdr.functions_def import get_hangupcause_id

logger = logging.getLogger('cdr-stats.filelog')


class CdrResource(ModelResource):

    """API to bulk create cdr

    **Attributes**:

        * ``accountcode`` -
        * ``answer_uepoch`` -
        * ``billmsec`` -
        * ``billsec`` -
        * ``caller_id_name`` -
        * ``caller_id_number`` -
        * ``cdr_object_id`` -
        * ``cdr_type`` -
        * ``destination_number`` -
        * ``direction":"inbound`` -
        * ``duration`` -
        * ``end_uepoch`` -
        * ``hangup_cause_id`` -
        * ``mduration`` -
        * ``read_codec`` -
        * ``remote_media_ip`` -
        * ``start_uepoch`` -
        * ``switch_id`` -
        * ``uuid``
        * ``write_codec`` -

    **Validation**:

        * CdrValidation()

    **CURL Usage**::

        curl -u username:password --dump-header - -H "Content-Type:application/json" -X POST --data '{"switch_id": 1, "caller_id_number": 12345, "caller_id_name": "xyz", "destination_number": 9972374874, "duration": 12, "billsec": 15, "hangup_cause_q850": 16, "accountcode": 32523, "direction": "IN", "uuid": "e8fee8f6-40dd-11e1-964f-000c296bd875", "remote_media_ip": "127.0.0.1", "start_uepoch": "2012-02-20 12:23:34", "answer_uepoch": "2012-02-20 12:23:34", "end_uepoch": "2012-02-20 12:23:34", "mduration": 32, "billmsec": 43, "read_codec": "xyz", "write_codec": "abc", "cdr_type": 1}' http://localhost:8000/api/v1/cdr/

    **Response**::

        {
           "_id":"4f3dec801d41c80b8e000000",
           "accountcode":"1000",
           "answer_uepoch":"2012-01-25T14:05:53",
           "billmsec":"12960",
           "billsec":13,
           "caller_id_name":"1000",
           "caller_id_number":"1000",
           "cdr_object_id":"4f3dec231d41c80b2600001f",
           "cdr_type":1,
           "destination_number":"5545",
           "direction":"inbound",
           "duration":107,
           "end_uepoch":"2012-01-25T14:06:06",
           "hangup_cause_id":8,
           "mduration":"12960",
           "read_codec":"G722",
           "remote_media_ip":"192.168.1.21",
           "start_uepoch":"2012-02-15T22:02:51",
           "switch_id":1,
           "uuid":"2ffd8364-592c-11e1-964f-000c296bd875",
           "write_codec":"G722"
        }
    """
    class Meta:
        resource_name = 'cdr'
        authorization = Authorization()
        authentication = BasicAuthentication()
        allowed_methods = ['post']
        throttle = BaseThrottle(throttle_at=1000, timeframe=3600)  # default 1000 calls / hour

    def override_urls(self):

        return [url(r'^(?P<resource_name>%s)/$' % self._meta.resource_name,
            self.wrap_view('create'))]

    def create_response(self, request, data, response_class=HttpResponse,
                        **response_kwargs):

        desired_format = self.determine_format(request)
        serialized = self.serialize(request, data, desired_format)
        return response_class(content=serialized, content_type=desired_format,
            **response_kwargs)

    def create(self, request=None, **kwargs):
        logger.debug('CDR API get called')

        j = 0
        post_var = {}
        for i in request.POST:
            if j == 0:
                post_var = i
                j = j + 1

        import ast
        post_var = ast.literal_eval(post_var)

        switch_id = post_var.get('switch_id')
        caller_id_number = post_var.get('caller_id_number')
        caller_id_name = post_var.get('caller_id_name')
        destination_number = post_var.get('destination_number')
        duration = post_var.get('duration')
        billsec = post_var.get('billsec')
        hangup_cause_q850 = post_var.get('hangup_cause_q850')
        accountcode = post_var.get('accountcode')
        direction = post_var.get('direction')
        uuid = post_var.get('uuid')
        remote_media_ip = post_var.get('remote_media_ip')
        start_uepoch = post_var.get('start_uepoch')
        answer_uepoch = post_var.get('answer_uepoch')
        end_uepoch = post_var.get('end_uepoch')
        mduration = post_var.get('mduration')
        billmsec = post_var.get('billmsec')
        read_codec = post_var.get('read_codec')
        write_codec = post_var.get('write_codec')
        cdr_type = post_var.get('cdr_type')

        cdr_record = {
            'switch_id': switch_id,
            'caller_id_number': caller_id_number,
            'caller_id_name': caller_id_name,
            'destination_number': destination_number,
            'duration': int(duration),
            'billsec': int(billsec),
            'hangup_cause_id': get_hangupcause_id(hangup_cause_q850),
            'accountcode': accountcode,
            'direction': direction,
            'uuid': uuid,
            'remote_media_ip': remote_media_ip,
            'start_uepoch': start_uepoch,
            'answer_uepoch': answer_uepoch,
            'end_uepoch': end_uepoch,
            'mduration': mduration,
            'billmsec': billmsec,
            'read_codec': read_codec,
            'write_codec': write_codec,
            'cdr_type': cdr_type,
            }

        # Create CDR record
        settings.DBCON[settings.MG_CDR_COMMON].insert(cdr_record)
        # get last inserted cdr record
        new_obj = settings.DBCON[settings.MG_CDR_COMMON].find_one()

        # print new_obj['_id']
        logger.debug('CDR API : result ok 200')
        return self.create_response(request, new_obj)
