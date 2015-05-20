#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2015 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from voip_billing.models import VoIPRetailRate, find_rates
from cdr.functions_def import prefix_list_string
from voip_billing.function_def import prefix_allowed_to_call
import logging

logger = logging.getLogger('cdr-stats.filelog')


class VoIPRateList(APIView):

    """
    List all voip rate

    **Read**:

            CURL Usage::

                curl -u username:password -H 'Accept: application/json'
                http://localhost:8000/rest-api/voip-rate/?recipient_phone_no=4323432&sort_field=prefix&order=desc

                curl -u username:password -H 'Accept: application/json'
                http://localhost:8000/rest-api/voip-rate/?dialcode=4323432&sort_field=prefix&order=desc
    """
    authentication = (BasicAuthentication, SessionAuthentication)

    def get(self, request, format=None):
        """
        Voip Rate GET
        """
        logger.debug('Voip Rate GET API get called')
        error = {}

        # check voipplan id for user
        try:
            voipplan_id = request.user.userprofile.voipplan_id
        except:
            error_msg = "User is not attached with voip plan"
            error['error'] = error_msg
            return Response(error)

        dialcode = ''
        recipient_phone_no = ''
        if 'dialcode' in request.GET and request.GET.get('dialcode') != '':
            dialcode = request.GET.get('dialcode')
            try:
                dialcode = int(dialcode)
            except ValueError:
                error['error'] = "Wrong value for dialcode !"
                logger.error(error['error'])
                return Response(error)

        if 'recipient_phone_no' in request.GET:
            if request.GET.get('recipient_phone_no') != '':
                recipient_phone_no = request.GET.get('recipient_phone_no')
            else:
                error['error'] = "Please enter recipient_phone_no"
                logger.error(error['error'])
                return Response(error)

        if recipient_phone_no:
            # Check if recipient_phone_no is not banned
            allowed = prefix_allowed_to_call(recipient_phone_no, voipplan_id)
            if allowed:
                # Get Destination prefix list e.g (34,346,3465,34657)
                destination_prefix_list = prefix_list_string(str(recipient_phone_no))
                prefixlist = destination_prefix_list.split(",")
                # Get Rate List
                rate_list = VoIPRetailRate.objects\
                    .values('prefix', 'retail_rate', 'prefix__destination')\
                    .filter(prefix__in=[int(s) for s in prefixlist])
                logger.debug('Voip Rate API : result OK 200')
                return Response(rate_list)
            else:
                error_msg = "Not allowed : %s" % recipient_phone_no
                error['error'] = error_msg
                logger.error(error_msg)
                return Response(error)

        sort_field = ''
        order = ''
        if request.GET.get('sort_field'):
            sort_field = request.GET.get('sort_field')
        if request.GET.get('order'):
            order = request.GET.get('order')

        # call the find rates function
        result = find_rates(voipplan_id, dialcode, sort_field, order)

        logger.debug('Voip Rate API : result OK 200')
        return Response(result)
