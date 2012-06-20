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
from tastypie.resources import ModelResource
from tastypie.throttle import BaseThrottle
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import Authorization

from cdr.models import HangupCause


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
        # default 1000 calls / hour
        throttle = BaseThrottle(throttle_at=1000, timeframe=3600)
