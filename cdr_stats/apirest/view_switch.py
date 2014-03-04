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
from rest_framework import viewsets
from apirest.switch_serializers import SwitchSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from cdr.models import Switch
#from permissions import CustomObjectPermissions


class SwitchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Switch to be viewed or edited.
    """
    model = Switch
    queryset = Switch.objects.all()
    serializer_class = SwitchSerializer
    authentication = (BasicAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated)
