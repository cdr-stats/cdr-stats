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

from django.conf.urls import url
from django.db import connection
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from tastypie.throttle import BaseThrottle
from tastypie.exceptions import BadRequest, ImmediateHttpResponse
from tastypie import http
from api.resources import IpAddressAuthentication
from voip_billing.models import VoIPRetailRate
from voip_billing.function_def import prefix_allowed_to_call, prefix_list_string
from user_profile.models import UserProfile
import logging

logger = logging.getLogger('cdr-stats.filelog')


class VoipRateResource(ModelResource):
    """API to get voip call rate via dialcode or recipient_phone_no

    **Attributes**:

        * ``dialcode`` -
        * ``recipient_phone_no`` -

    **Create**:

         CURL Usage::

             curl -u username:password -H 'Accept: application/json' http://localhost:8000/api/v1/voip_rate/dialcode/34/?format=json

                 or

             curl -u username:password -H 'Accept: application/json' http://localhost:8000/api/v1/voip_rate/?format=json

                or

             curl -u username:password -H 'Accept: application/json' http://localhost:8000/api/v1/voip_rate/recipient_phone_no/34650784355/?format=json

         Response::

            [
               {
                  "prefix":34,
                  "prefix__destination":"Spain",
                  "retail_rate":"0.0350"
               },
               {
                  "prefix":33,
                  "prefix__destination":"France",
                  "retail_rate":"0.0984"
               },
               {
                  "prefix":32,
                  "prefix__destination":"Belgium",
                  "retail_rate":"0.0744"
               },
               {
                  "prefix":39,
                  "prefix__destination":"Italy",
                  "retail_rate":"0.0720"
               }
            ]

        Response::

            [
               {
                  "prefix":34,
                  "prefix__destination":"Spain",
                  "retail_rate":"0.0350"
               }
            ]

    """
    class Meta:
        resource_name = 'voip_rate'
        authorization = Authorization()
        authentication = IpAddressAuthentication()
        allowed_methods = ['get']
        detail_allowed_methods = ['get']
        throttle = BaseThrottle(throttle_at=1000, timeframe=3600)  # default 1000 calls / hour

    def override_urls(self):
        """Override urls"""
        return [
            url(r'^(?P<resource_name>%s)/$' % self._meta.resource_name,
                self.wrap_view('read')),
            url(r'^(?P<resource_name>%s)/dialcode/(.+)/$' % self._meta.resource_name,
                self.wrap_view('read')),
            url(r'^(?P<resource_name>%s)/recipient_phone_no/(.+)/$' % self._meta.resource_name,
                self.wrap_view('read')),
        ]

    def read(self, request=None, **kwargs):
        """API to get voip call rate via dialcode or recipient_phone_no"""
        logger.debug('Voip Rate GET API get called')
        auth_result = self._meta.authentication.is_authenticated(request)
        if not auth_result is True:
            raise ImmediateHttpResponse(response=http.HttpUnauthorized())

        logger.debug('Voip Rate GET API authorization called!')
        auth_result = self._meta.authorization.is_authorized(request, object)

        user_profile = UserProfile.objects.get(user=request.user)
        voipplan_id = user_profile.voipplan_id
        if voipplan_id is None:
            error_msg = "User is not attached with voip plan \n"
            logger.error(error_msg)
            raise BadRequest(error_msg)

        dialcode = ''
        recipient_phone_no = ''
        if '/dialcode/' in request.META['PATH_INFO']:
            dialcode = request.META['PATH_INFO'].split('/api/v1/voip_rate/dialcode/')[1].split('/')[0]
        if '/recipient_phone_no/' in request.META['PATH_INFO']:
            recipient_phone_no = request.META['PATH_INFO']\
                .split('/api/v1/voip_rate/recipient_phone_no/')[1]\
                .split('/')[0]

        if recipient_phone_no:
            #Check if recipient_phone_no is not banned
            allowed = prefix_allowed_to_call(recipient_phone_no, voipplan_id)
            if allowed:
                #Get Destination prefix list e.g (34,346,3465,34657)
                destination_prefix_list = prefix_list_string(str(recipient_phone_no))
                prefixlist = destination_prefix_list.split(",")
                #Get Rate List
                rate_list = VoIPRetailRate.objects.values('prefix', 'retail_rate', 'prefix__destination').filter(prefix__in=[int(s) for s in prefixlist])
                logger.debug('Voip Rate API : result OK 200')
                return self.create_response(request, rate_list)
            else:
                error_msg = "Not allowed : %s" % recipient_phone_no
                logger.error(error_msg)
                raise BadRequest(error_msg)

        cursor = connection.cursor()
        if dialcode:
            try:
                dialcode = int(dialcode)
            except ValueError:
                error_msg = "Wrong value for dialcode !"
                logger.error(error_msg)
                raise BadRequest(error_msg)

            sqldialcode = str(dialcode) + '%'
            sql_statement = (
                "SELECT voipbilling_voip_retail_rate.prefix, "
                "Min(retail_rate) as minrate, dialcode_prefix.destination "
                "FROM voipbilling_voip_retail_rate "
                "INNER JOIN voipbilling_voipplan_voipretailplan "
                "ON voipbilling_voipplan_voipretailplan.voipretailplan_id = "
                "voipbilling_voip_retail_rate.voip_retail_plan_id "
                "LEFT JOIN dialcode_prefix ON dialcode_prefix.prefix = "
                "voipbilling_voip_retail_rate.prefix "
                "WHERE voipplan_id=%s "
                "AND CAST(voipbilling_voip_retail_rate.prefix AS TEXT) LIKE %s "
                "GROUP BY voipbilling_voip_retail_rate.prefix, dialcode_prefix.destination;")

            cursor.execute(sql_statement, [voipplan_id, sqldialcode])
        else:
            sql_statement = (
                'SELECT voipbilling_voip_retail_rate.prefix, '
                'Min(retail_rate) as minrate, dialcode_prefix.destination '
                'FROM voipbilling_voip_retail_rate '
                'INNER JOIN voipbilling_voipplan_voipretailplan '
                'ON voipbilling_voipplan_voipretailplan.voipretailplan_id = '
                'voipbilling_voip_retail_rate.voip_retail_plan_id '
                'LEFT JOIN dialcode_prefix ON dialcode_prefix.prefix = '
                'voipbilling_voip_retail_rate.prefix '
                'WHERE voipplan_id=%s '
                'GROUP BY voipbilling_voip_retail_rate.prefix, dialcode_prefix.destination')

            cursor.execute(sql_statement, [voipplan_id])

        row = cursor.fetchall()

        result = []
        for record in row:
            # Not banned Prefix
            allowed = prefix_allowed_to_call(record[0], voipplan_id)

            if allowed:
                modrecord = {}
                modrecord['prefix'] = record[0]
                modrecord['retail_rate'] = record[1]
                modrecord['prefix__destination'] = record[2]
                result.append(modrecord)

        logger.debug('Voip Rate API : result OK 200')
        return self.create_response(request, result)
