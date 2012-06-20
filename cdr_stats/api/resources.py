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

from django.contrib.auth.models import User
from django.conf import settings
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization
from tastypie.serializers import Serializer
from tastypie.exceptions import ImmediateHttpResponse
from tastypie import http
from random import seed
import urllib
import simplejson
import logging

logger = logging.getLogger('cdr-stats.filelog')

seed()


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
        if request.META['REMOTE_ADDR'] in settings.API_ALLOWED_IP:
            return True
        else:
            raise ImmediateHttpResponse(response=http.HttpUnauthorized())
            return False


class IpAddressAuthentication(Authentication):

    def is_authorized(self, request, object=None):
        if request.META['REMOTE_ADDR'] in settings.API_ALLOWED_IP:
            return True
        else:
            raise ImmediateHttpResponse(response=http.HttpUnauthorized())
            return False


def get_contact(id):
    try:
        con_obj = User.objects.get(pk=id)
        return con_obj.username
    except:
        return ''
