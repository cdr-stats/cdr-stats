from piston.handler import BaseHandler
from piston.emitters import *
from piston.utils import rc, require_mime, require_extended, throttle
from voip_billing.models import VoIPRetailRate
from voip_report.models import VoIPCall, VoIPCall_Report
from voip_billing.tasks import VoIPbilling
from voip_billing.function_def import prefix_allowed_to_voip_call, prefix_list_string
from user_profile.models import UserProfile
from datetime import datetime


class VoIPRateHandler(BaseHandler):
    """
    Handler to get rate for sending SMS
    """
    #model = SmsRetailRate
    fields = ('prefix', 'retail_rate', 'prefix__destination')
    allowed_methods = ('GET', 'POST')

    @throttle(30, 1*60) # Throttle if more that 30 times within 1 minute
    def read(self, request, code=None):
        """
        Get All Rate to make VoIP Call

        Parameters :
        [ ]

        CURL Testing :
            curl -u username:password -i -H "Accept: application/json" -X GET http://127.0.0.1:8000/voip_billing/api/voiprate/

            or with prefix

            curl -u username:password -i -H "Accept: application/json" -X GET http://127.0.0.1:8000/voip_billing/api/voiprate/XXX/
        """
        user_voip_plan = UserProfile.objects.get(user=request.user)
        voipplan_id = user_voip_plan.voipplan_id #  1

        from django.db import connection, transaction
        cursor = connection.cursor()
        if code :
            try:
                code = int(code)
            except ValueError:
                resp = rc.BAD_REQUEST
                resp.write("\nError on the code parameter!")
                return resp
            sql_statement = ('SELECT voipbilling_voip_retail_rate.prefix, '\
                'Min(retail_rate) as minrate, simu_prefix.destination '\
                'FROM voipbilling_voip_retail_rate '\
                'INNER JOIN voipbilling_voipplan_voipretailplan '\
                'ON voipbilling_voipplan_vopiretailplan.voipretailplan_id = '\
                'voipbilling_voip_retail_rate.voip_retail_plan_id '\
                'LEFT JOIN simu_prefix ON simu_prefix.prefix =  '\
                'voipbilling_voip_retail_rate.prefix '\
                'WHERE voipplan_id=%s '\
                'AND voipbilling_voip_retail_rate.prefix LIKE %s '\
                'GROUP BY voipbilling_voip_retail_rate.prefix')
            q = str(code) + '%'
            cursor.execute(sql_statement, [voipplan_id, q])
        else :
            sql_statement = ('SELECT voipbilling_voip_retail_rate.prefix, '\
                'Min(retail_rate) as minrate, simu_prefix.destination '\
                'FROM voipbilling_voip_retail_rate '\
                'INNER JOIN voipbilling_voipplan_voipretailplan '\
                'ON voipbilling_voipplan_voipretailplan.voipretailplan_id = '\
                'voipbilling_voip_retail_rate.voip_retail_plan_id '\
                'LEFT JOIN simu_prefix ON simu_prefix.prefix =  '\
                'voipbilling_voip_retail_rate.prefix '\
                'WHERE voipplan_id=%s '\
                'GROUP BY voipbilling_voip_retail_rate.prefix')
            cursor.execute(sql_statement, [voipplan_id,])
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
        return result
        
    def create(self, request):
        """
        Get Rate to VoIP Call

        Parameters :
        [ Prefix ]

        CURL Testing :
        curl -u username:password -i -H "Accept: application/json" \
        -X POST http://127.0.0.1:8000/voip_billing/api/voiprate/ \
        -d "recipient_phone_no=xxxxxxxxxxxx"
        """
        attrs = self.flatten_dict(request.POST)
        recipient_phone_no = attrs['recipient_phone_no']

        user_voip_plan = UserProfile.objects.get(user=request.user)
        voipplan_id = user_voip_plan.voipplan_id #  1

        # Should Not banned recipient_phone_no
        allowed = prefix_allowed_to_voip_call(recipient_phone_no, voipplan_id)

        if allowed:
            # Get Destination prefix list e.g (34,346,3465,34657)
            destination_prefix_list = prefix_list_string(str(recipient_phone_no))

            # Split Destination prefix list
            list = destination_prefix_list.split(",")

            # Get Rate List
            rate_list = VoipRetailRate.objects.values('prefix', 'retail_rate',
                'prefix__destination').filter(prefix__in=[int(s) for s in list])

            try:
                return rate_list
            except:
                return rc.BAD_REQUEST
        else:
            return rc.BAD_REQUEST


class BillVoIPCallHandler(BaseHandler):
    """
    Handler to import VoIP Call report
    """
    allowed_methods = ('POST', )

    def create(self, request):
        """
        To import and bill VoIP call from an other system

        Parameters :
        [ Recipient Phone No, Sender Phone No, disposition, call date ]

        CURL Testing :
        curl -u username:password -i -H "Accept: application/json" \
        -X POST http://127.0.0.1:8000/voip_billing/api/bill_voipcall/ \
        -d "recipient_phone_no=xxxxxxxxxxxxx&sender_phone_no=xxxxxxxxxxxxx\
        &disposition=1&call_date=YYYY-MM-DD HH:MM:SS"

        DISPOSITION - [(1, 'ANSWER'), (2, 'BUSY'), (3, 'NOANSWER'),
        (4, 'CANCEL'), (5, 'CONGESTION'), (6, 'CHANUNAVAIL'), (7, 'DONTCALL'),
        (8, 'TORTURE'), (9, 'INVALIDARGS'), (20,'NOROUTE'), (30,'FORBIDDEN')]
        """
        attrs = self.flatten_dict(request.POST)
        recipient_phone_no = attrs['recipient_phone_no']
        sender_phone_no = attrs['sender_phone_no']        
        disposition_status = attrs['disposition']
        call_date = datetime.strptime(attrs['call_date'],
                                          '%Y-%m-%d %H:%M:%S')
        user_voip_plan = UserProfile.objects.get(user=request.user)
        voipplan_id = user_voip_plan.voipplan_id #  1

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
                response = \
                voipcall._update_voip_call_status(res['voipcall_id'])
                
                resp = rc.CREATED
                resp.write("Call Record saved!")
                return resp
            else:
                msg = 'Error : Please Start Celeryd Service'
                #TODO : log the error
                resp = rc.FORBIDDEN
                resp.write("\nInternal error!")
                return resp
        except:            
            return rc.BAD_REQUEST
