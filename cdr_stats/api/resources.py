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
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

import logging

from django.contrib.auth.models import User
from django.conf.urls.defaults import url
from django.http import HttpResponse, HttpResponseNotFound
from django.conf import settings

from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.authentication import Authentication, BasicAuthentication
from tastypie.authorization import Authorization, DjangoAuthorization
from tastypie.serializers import Serializer
from tastypie.validation import Validation
from tastypie.throttle import BaseThrottle
from tastypie.utils import dict_strip_unicode_keys, trailing_slash
from tastypie.http import HttpCreated, HttpNoContent, HttpNotFound, \
    HttpBadRequest
from tastypie.exceptions import BadRequest, NotFound, ImmediateHttpResponse
from tastypie import http
from tastypie import fields

from cdr.models import Switch, HangupCause
from cdr.functions_def import get_hangupcause_id

from settings import API_ALLOWED_IP
from datetime import datetime
from random import choice, seed

import urllib
import simplejson

seed()

logger = logging.getLogger('cdr-stats.filelog')

#TODO : Split ressources in different files

class CustomJSONSerializer(Serializer):

    def from_json(self, content):
        decoded_content = urllib.unquote(content.decode('utf8'))
        # data = simplejson.loads(content)
        data = {}
        data['cdr'] = decoded_content[4:]
        return data


def get_attribute(attrs, attr_name):
    """this is a helper to retrieve an attribute if it exists"""
    if attr_name in attrs:
        attr_value = attrs[attr_name]
    else:
        attr_value = None
    return attr_value


def get_value_if_none(x, value):
    """return value if x is None"""
    if x is None:
        return value
    return x


def save_if_set(record, fproperty, value):
    """function to save a property if it has been set"""
    if value:
        record.__dict__[fproperty] = value


class IpAddressAuthorization(Authorization):

    def is_authorized(self, request, object=None):
        if request.META['REMOTE_ADDR'] in API_ALLOWED_IP:
            return True
        else:
            raise ImmediateHttpResponse(response=http.HttpUnauthorized())
            return False


class IpAddressAuthentication(Authentication):

    def is_authorized(self, request, object=None):
        if request.META['REMOTE_ADDR'] in API_ALLOWED_IP:
            return True
        else:
            raise ImmediateHttpResponse(response=http.HttpUnauthorized())
            return False


class UserResource(ModelResource):

    """User Model"""

    class Meta:

        allowed_methods = ['get']
        queryset = User.objects.all()
        resource_name = 'user'
        fields = ['username', 'first_name', 'last_name', 'last_login', 'id']
        filtering = {'username': 'exact'}
        throttle = BaseThrottle(throttle_at=1000, timeframe=3600)  # default 1000 calls / hour


class SwitchResource(ModelResource):

    """
    **Attributes Details**:

        * ``name`` - Name of switch.
        * ``ipaddress`` - ipaddress

    **Read**:

        CURL Usage::

            curl -u username:password -H 'Accept: application/json' -X GET http://localhost:8000/api/v1/switch/?format=json

    """

    class Meta:

        queryset = Switch.objects.all()
        resource_name = 'switch'
        authorization = Authorization()
        authentication = BasicAuthentication()
        list_allowed_methods = ['get', 'post', 'put', 'delete']
        detail_allowed_methods = ['get', 'post', 'put', 'delete']
        throttle = BaseThrottle(throttle_at=1000, timeframe=3600)  # default 1000 calls / hour


class HangupCauseResource(ModelResource):

    """
    **Attributes Details**:

        * ``code`` - ITU-T Q.850 Code.
        * ``enumeration`` - Enumeration
        * ``cause`` - cause
        * ``description`` - cause description

    **Read**:

        CURL Usage::

            curl -u username:password -H 'Accept: application/json' -X GET http://localhost:8000/api/v1/hangup_cause/?format=json

    """

    class Meta:

        queryset = HangupCause.objects.all()
        resource_name = 'hangup_cause'
        authorization = Authorization()
        authentication = BasicAuthentication()
        list_allowed_methods = ['get', 'post', 'put', 'delete']
        detail_allowed_methods = ['get', 'post', 'put', 'delete']
        throttle = BaseThrottle(throttle_at=1000, timeframe=3600)  # default 1000 calls / hour


def get_contact(id):
    try:
        con_obj = User.objects.get(pk=id)
        return con_obj.username
    except:
        return ''


class CdrDailyResource(ModelResource):

    """
    **Attributes Details**:

        * ``_id`` - contact id
        * ``start_uepoch`` - call date
        * ``destination_number`` - destination
        * ``hangup_cause_id`` -
        * ``switch_id`` - switch

    **Read**:

            CURL Usage::

                curl -u username:password -H 'Accept: application/json' -X POST --data '{"start_uepoch":"2012-02-15", "switch_id": 1, "destination_number": 3000, "accountcode": 123}' http://localhost:8000/api/v1/cdr_daily_report/

            Response::

                [
                   {
                      "_id":"4f3dec808365701c4a25aaad",
                      "accountcode":"1000",
                      "destination_number":"5545",
                      "hangup_cause_id":8,
                      "start_uepoch":"2012-02-15T00:00:00",
                      "switch_id":1
                   },
                   {
                      "_id":"4f3dec808365701c4a25aab0",
                      "accountcode":"1000",
                      "destination_number":"2133",
                      "hangup_cause_id":9,
                      "start_uepoch":"2012-02-15T00:00:00",
                      "switch_id":1
                   }
                ]

    """

    class Meta:

        resource_name = 'cdr_daily_report'
        authorization = Authorization()
        authentication = BasicAuthentication()
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        throttle = BaseThrottle(throttle_at=1000, timeframe=3600)  # default 1000 calls / hour

    def override_urls(self):

        return [url(r'^(?P<resource_name>%s)/$' % self._meta.resource_name,
                self.wrap_view('read'))]

    def read_response(self, request, data, response_class=HttpResponse,
                      **response_kwargs):

        desired_format = self.determine_format(request)
        serialized = self.serialize(request, data, desired_format)
        return response_class(content=serialized, content_type=desired_format,
                              **response_kwargs)

    def read(self, request=None, **kwargs):

        logger.debug('CDR Daily Report API get called')
        auth_result = self._meta.authentication.is_authenticated(request)
        if not auth_result is True:
            raise ImmediateHttpResponse(response=http.HttpUnauthorized())

        logger.debug('CDR Daily Report API authorization called!')
        auth_result = self._meta.authorization.is_authorized(request, object)

        j = 0
        temp_var = {}
        for i in request.POST:
            if j == 0:
                temp_var = i
                j = j + 1

        import ast
        temp_var = ast.literal_eval(temp_var)

        query_var = {}
        if 'start_uepoch' in temp_var:
            query_var['start_uepoch'] = \
                datetime.strptime(temp_var['start_uepoch'], '%Y-%m-%d')
        if 'destination_number' in query_var:
            query_var['destination_number'] = int(temp_var['destination_number'
                    ])
        if 'accountcode' in query_var:
            query_var['accountcode'] = int(temp_var['accountcode'])
        if 'switch_id' in query_var:
            query_var['switch_id'] = int(temp_var['switch_id'])

        daily_data = settings.DBCON[settings.MG_CDR_DAILY]

        if query_var:
            daily_data = daily_data.find(query_var)
        else:
            daily_data = daily_data.find()
        # calls_in_day = daily_data.map_reduce(map, reduce, out, query=query_var)

        result = []
        for record in daily_data:
            modrecord = {}
            modrecord['_id'] = record['_id']
            modrecord['start_uepoch'] = record['start_uepoch']
            modrecord['destination_number'] = record['destination_number']
            modrecord['hangup_cause_id'] = record['hangup_cause_id']
            modrecord['accountcode'] = record['accountcode']
            modrecord['switch_id'] = record['switch_id']

            result.append(modrecord)

        logger.debug('CDR Daily Report API : result ok 200')
        return self.read_response(request, result)


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
