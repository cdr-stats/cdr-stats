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

from pymongo.connection import Connection
from pymongo.errors import ConnectionFailure

logger = logging.getLogger('cdr-stats.filelog')


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
        #list_allowed_methods = ['get']
        #detail_allowed_methods = ['get']
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
            start_date = datetime(int(temp_var['start_uepoch'][0:4]),
                                  int(temp_var['start_uepoch'][5:7]),
                                  int(temp_var['start_uepoch'][8:10]), 0, 0, 0, 0)
            end_date = datetime(int(temp_var['start_uepoch'][0:4]),
                                int(temp_var['start_uepoch'][5:7]),
                                int(temp_var['start_uepoch'][8:10]), 23, 59, 59, 999999)
            query_var['start_uepoch'] = {'$gte': start_date, '$lt': end_date}

        if 'destination_number' in query_var:
            query_var['destination_number'] = int(temp_var['destination_number'])
        if 'accountcode' in query_var:
            query_var['accountcode'] = int(temp_var['accountcode'])
        if 'switch_id' in query_var:
            query_var['switch_id'] = int(temp_var['switch_id'])

        daily_data = settings.DBCON[settings.MG_CDR_COMMON]

        if query_var:
            daily_data = daily_data.find(query_var)
            for record in daily_data.clone():
                print record
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
