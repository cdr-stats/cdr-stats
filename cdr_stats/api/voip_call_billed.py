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
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import Authorization
from tastypie.validation import Validation
from tastypie.throttle import BaseThrottle

from voip_billing.function_def import check_celeryd_process
from voip_billing.tasks import VoIPbilling
from voip_report.models import VoIPCall, VoIPCall_Report
from user_profile.models import UserProfile
from datetime import datetime
import logging
logger = logging.getLogger('cdr-stats.filelog')


class VoipCallBilledValidation(Validation):
    """
    Voip Call Billed Validation Class
    """

    def is_valid(self, bundle, request=None):
        errors = {}
        if not bundle.data:
            errors['Data'] = ['Data set is empty']

        user_profile = UserProfile.objects.get(user=request.user)
        voipplan_id = user_profile.voipplan_id
        if voipplan_id is None:
            errors['user_error'] = ["User is not attached with voip plan"]

        return errors


class VoipCallBilledResource(ModelResource):
    """API to create voip cdr record and bill it

    **Attributes**:

        * ``recipient_phone_no`` -
        * ``sender_phone_no`` -
        * ``disposition`` -
        * ``call_date`` -


    **Create**:

         CURL Usage::

             curl -u username:password --dump-header - -H "Content-Type:application/json" -X POST --data '{"recipient_phone_no": "34657077888", "sender_phone_no": "919427164510", "disposition": "1", "call_date": "2013-01-11 11:11:22"}' http://localhost:8000/api/v1/voip_call_billed/

         Response::

            HTTP/1.0 201 CREATED
            Date: Fri, 18 Jan 2013 08:09:53 GMT
            Server: WSGIServer/0.1 Python/2.7.3
            Vary: Accept-Language, Cookie
            Content-Type: text/html; charset=utf-8
            Location: http://localhost:8000/api/v1/voip_call_billed/None/
            Content-Language: en-us

    """
    class Meta:
        resource_name = 'voip_call_billed'
        queryset = VoIPCall_Report.objects.all()
        authorization = Authorization()
        authentication = BasicAuthentication()
        allowed_methods = ['post']
        detail_allowed_methods = ['post']
        throttle = BaseThrottle(throttle_at=1000, timeframe=3600)  # default 1000 calls / hour

    def obj_create(self, bundle, request=None, **kwargs):
        """
        A ORM-specific implementation of ``obj_create``.
        """
        logger.debug('VoIPCall Report API get called')

        bundle.obj = self._meta.object_class()
        bundle = self.full_hydrate(bundle)

        recipient_phone_no = bundle.data.get('recipient_phone_no')
        sender_phone_no = bundle.data.get('sender_phone_no')
        disposition_status = bundle.data.get('disposition')
        call_date = datetime.strptime(bundle.data.get('call_date'),
            '%Y-%m-%d %H:%M:%S')

        voipplan_id = UserProfile.objects.get(user=request.user).voipplan_id

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
            logger.debug('VoIPCall Report API : result ok 200')

        logger.debug('VoIPCall Report API : result ok 200')
        return obj