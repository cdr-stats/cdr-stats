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

from django.conf.urls import url
from django.http import HttpResponse
from django.db import connection

from tastypie.resources import ModelResource
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import Authorization
from tastypie.throttle import BaseThrottle
from tastypie.exceptions import BadRequest, ImmediateHttpResponse
from tastypie import http
from voip_billing.models import VoIPRetailRate
from voip_billing.function_def import prefix_allowed_to_voip_call
from user_profile.models import UserProfile

import logging
logger = logging.getLogger('cdr-stats.filelog')


class VoipRateResource(ModelResource):
    """API to bulk create cdr

    **Attributes**:

        * ``accountcode`` -
        * ``answer_uepoch`` -
        * ``billmsec`` -


    **Read**:

         CURL Usage::

             curl -u username:password -H 'Accept: application/json' http://localhost:8000/api/v1/voip_rate/%code%/?format=json

                 or

             curl -u username:password -H 'Accept: application/json' http://localhost:8000/api/v1/voip_rate/?format=json

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


    """
    class Meta:
        resource_name = 'voip_rate'
        #queryset = VoIPRetailRate.objects.all()
        authorization = Authorization()
        authentication = BasicAuthentication()
        allowed_methods = ['get']
        detail_allowed_methods = ['get']
        throttle = BaseThrottle(throttle_at=1000, timeframe=3600)  # default 1000 calls / hour

    def override_urls(self):
        """Override urls"""
        return [
            url(r'^(?P<resource_name>%s)/$' %\
                self._meta.resource_name, self.wrap_view('read')),
            ]

    def read_response(self, request, data,
                      response_class=HttpResponse, **response_kwargs):
        """To display API's result"""
        desired_format = self.determine_format(request)
        serialized = self.serialize(request, data, desired_format)
        return response_class(content=serialized,
            content_type=desired_format, **response_kwargs)

    def read(self, request=None, **kwargs):
        """GET method of Subscriber API"""
        logger.debug('Voip Rate GET API get called')
        auth_result = self._meta.authentication.is_authenticated(request)
        if not auth_result is True:
            raise ImmediateHttpResponse(response=http.HttpUnauthorized())

        logger.debug('Voip Rate GET API authorization called!')
        auth_result = self._meta.authorization.is_authorized(request, object)


        user_voip_plan = UserProfile.objects.get(user=request.user)
        voipplan_id = user_voip_plan.voipplan_id #  1

        temp_url = request.META['PATH_INFO']
        temp_id = temp_url.split('/api/v1/voip_rate/')[1]
        code = temp_id.split('/')[0]

        cursor = connection.cursor()

        if code :
            try:
                code = int(code)
            except ValueError:
                error_msg = "Wrong value for code !"
                logger.error(error_msg)
                raise BadRequest(error_msg)
            """
            # for mysql
            q =  str(code) + '%'
            sql_statement = ('SELECT voipbilling_voip_retail_rate.prefix, '\
                             'Min(retail_rate) as minrate, dialcode_prefix.destination '\
                             'FROM voipbilling_voip_retail_rate '\
                             'INNER JOIN voipbilling_voipplan_voipretailplan '\
                             'ON voipbilling_voipplan_voipretailplan.voipretailplan_id = '\
                             'voipbilling_voip_retail_rate.voip_retail_plan_id '\
                             'LEFT JOIN dialcode_prefix ON dialcode_prefix.prefix =  '\
                             'voipbilling_voip_retail_rate.prefix '\
                             'WHERE voipplan_id=%s '\
                             'AND voipbilling_voip_retail_rate.prefix LIKE "%s" '\
                             'GROUP BY voipbilling_voip_retail_rate.prefix' \
                             % (voipplan_id, q))
            """
            # for postgre-sql
            q =  str(code) + '%'
            sql_statement = ("SELECT voipbilling_voip_retail_rate.prefix, "\
                             "Min(retail_rate) as minrate, dialcode_prefix.destination "\
                             "FROM voipbilling_voip_retail_rate "\
                             "INNER JOIN voipbilling_voipplan_voipretailplan "\
                             "ON voipbilling_voipplan_voipretailplan.voipretailplan_id = "\
                             "voipbilling_voip_retail_rate.voip_retail_plan_id "\
                             "LEFT JOIN dialcode_prefix ON dialcode_prefix.prefix =  "\
                             "voipbilling_voip_retail_rate.prefix "\
                             "WHERE voipplan_id=%s "\
                             "AND CAST(voipbilling_voip_retail_rate.prefix AS TEXT) LIKE %s "\
                             "GROUP BY voipbilling_voip_retail_rate.prefix, dialcode_prefix.destination;")

            cursor.execute(sql_statement, [voipplan_id, q])
        else:
            sql_statement = ('SELECT voipbilling_voip_retail_rate.prefix, '\
                             'Min(retail_rate) as minrate, dialcode_prefix.destination '\
                             'FROM voipbilling_voip_retail_rate '\
                             'INNER JOIN voipbilling_voipplan_voipretailplan '\
                             'ON voipbilling_voipplan_voipretailplan.voipretailplan_id = '\
                             'voipbilling_voip_retail_rate.voip_retail_plan_id '\
                             'LEFT JOIN dialcode_prefix ON dialcode_prefix.prefix =  '\
                             'voipbilling_voip_retail_rate.prefix '\
                             'WHERE voipplan_id=%s '\
                             'GROUP BY voipbilling_voip_retail_rate.prefix, dialcode_prefix.destination')

            cursor.execute(sql_statement, [voipplan_id])

        row = cursor.fetchall()

        result = []
        for record in row:
            # Not banned Prefix
            allowed = prefix_allowed_to_voip_call(record[0], voipplan_id)

            if allowed:
                modrecord = {}
                modrecord['prefix'] = record[0]
                modrecord['retail_rate'] = record[1]
                modrecord['prefix__destination'] = record[2]
                result.append(modrecord)

        logger.debug('Voip Rate API : result ok 200')
        return self.read_response(request, result)
