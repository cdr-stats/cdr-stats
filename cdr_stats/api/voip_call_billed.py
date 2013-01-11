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
from django.contrib.auth.models import User
from django.db import connection

from tastypie.resources import ModelResource
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import Authorization
from tastypie.throttle import BaseThrottle
from tastypie.exceptions import BadRequest, ImmediateHttpResponse
from tastypie.validation import Validation
from tastypie import http
from api.resources import IpAddressAuthorization, IpAddressAuthentication
from voip_billing.models import VoIPRetailRate
from voip_billing.function_def import prefix_allowed_to_voip_call, prefix_list_string,\
    check_celeryd_process
from voip_billing.tasks import VoIPbilling
from voip_report.models import VoIPCall, VoIPCall_Report
from user_profile.models import UserProfile
from datetime import datetime
import logging
logger = logging.getLogger('cdr-stats.filelog')


class VoipCallBilledResource(ModelResource):
    """API to bulk create cdr

    **Attributes**:

        * ``accountcode`` -
        * ``answer_uepoch`` -
        * ``billmsec`` -


    **Create**:

         CURL Usage::

             curl -u username:password --dump-header - -H "Content-Type:application/json" -X POST --data "ALegRequestUUID=48092924-856d-11e0-a586-0147ddac9d3e&CallUUID=48092924-856d-11e0-a586-0147ddac9d3e" http://localhost:8000/api/v1/voip_call_billed/

         Response::
    """
    class Meta:
        resource_name = 'voip_call_billed'
        authorization = Authorization()
        authentication = BasicAuthentication()
        allowed_methods = ['post']
        detail_allowed_methods = ['post']
        throttle = BaseThrottle(throttle_at=1000, timeframe=3600)  # default 1000 calls / hour

    def override_urls(self):
        """Override urls"""
        return [
            url(r'^(?P<resource_name>%s)/$' % self._meta.resource_name,
                self.wrap_view('create')),
            ]

    def create(self, request=None, **kwargs):
        """GET method of voip call get billed API"""
        logger.debug('Voip call billed API get called')
        auth_result = self._meta.authentication.is_authenticated(request)
        if not auth_result is True:
            raise ImmediateHttpResponse(response=http.HttpUnauthorized())

        logger.debug('Voip call billed API authorization called!')
        auth_result = self._meta.authorization.is_authorized(request, object)

        user_voip_plan = UserProfile.objects.get(user=request.user)
        voipplan_id = user_voip_plan.voipplan_id #  1


        recipient_phone_no = request.POST.get('recipient_phone_no')
        sender_phone_no = request.POST.get('sender_phone_no')
        disposition_status = request.POST.get('disposition')
        call_date = datetime.strptime(request.POST.get('call_date'),
            '%Y-%m-%d %H:%M:%S')

        try:
            if check_celeryd_process():
                # Create message record
                voipcall = VoIPCall.objects.create(
                    user=request.user,
                    recipient_number=recipient_phone_no,
                    callid=1,
                    callerid=sender_phone_no,
                    dnid=1,
                    nasipaddress='0.0.0.0',
                    sessiontime=1,
                    sessiontime_real=1,
                    disposition=disposition_status,)

                # Created task to bill VoIP Call
                response = VoIPbilling.delay(voipcall_id=voipcall.id,
                    voipplan_id=voipplan_id)

                # Due to task, message_id is disconnected/blank
                # So need to get back voipcall_id
                res = response.get()

                # Created VoIPCall Report record gets created date
                obj = VoIPCall_Report.objects.get(pk=res['voipcall_id'])
                obj.created_date = call_date
                obj.save()

                # Call status get changed according to status filed
                obj = voipcall._update_voip_call_status(res['voipcall_id'])
                logger.debug('Voip Rate API : result ok 200')


                result = []
                modrecord = {}
                modrecord['recipient_number'] = obj.recipient_number
                modrecord['disposition'] = obj.disposition
                modrecord['id'] = obj.id
                result.append(modrecord)
                return self.create_response(request, result)

            else:
                error_msg = "Error : Please Start Celeryd Service"
                logger.error(error_msg)
                raise BadRequest(error_msg)
        except:
            error_msg = "Error"
            logger.error(error_msg)
            raise BadRequest(error_msg)


