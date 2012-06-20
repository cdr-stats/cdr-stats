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
from tastypie.resources import ModelResource
from tastypie.throttle import BaseThrottle


class UserResource(ModelResource):
    """User Model

    **Read**:

        CURL Usage::

            curl -u username:password -H 'Accept: application/json' http://localhost:8000/api/v1/user/?format=json
    """
    class Meta:
        allowed_methods = ['get']
        queryset = User.objects.all()
        resource_name = 'user'
        fields = ['username', 'first_name', 'last_name', 'last_login', 'id']
        filtering = {'username': 'exact'}
        # default 1000 calls / hour
        throttle = BaseThrottle(throttle_at=1000, timeframe=3600)
