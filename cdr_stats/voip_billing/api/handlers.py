from piston.handler import BaseHandler
from piston.emitters import *
from piston.utils import rc, require_mime, require_extended, throttle
from voip_billing.models import VoIPRetailRate
from voip_report.models import VoIPCall, VoIPCall_Report
from voip_billing.tasks import VoIPbilling
from voip_billing.function_def import prefix_allowed_to_voip_call, prefix_list_string,\
    check_celeryd_process
from user_profile.models import UserProfile
from datetime import datetime



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
                response = voipcall._update_voip_call_status(res['voipcall_id'])
                
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
