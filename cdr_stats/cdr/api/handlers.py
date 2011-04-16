from piston.handler import BaseHandler, AnonymousBaseHandler
from piston.doc import generate_doc
from piston.emitters import *
from piston.utils import rc, require_mime, require_extended, throttle
from django.utils.translation import gettext as _
from cdr.models import CDR, dic_disposition
from datetime import *
from cdr.functions_def import *



def get_attribute(attrs, attr_name):
    """
    this is a helper to retrieve an attribute if it exists
    """
    if attrs.has_key(attr_name) : 
        attr_value = attrs[attr_name]
    else :
        attr_value = None
    return attr_value


class cdrHandler(BaseHandler):
    model = CDR
    allowed_methods = ('GET', 'POST',)
    #anonymous = 'AnonymousLanguageHandler'
    fields = ('src', 'dst', 'calldate', 'clid', 'dcontext', 'channel', \
        'dstchannel', 'lastapp', 'lastdata', 'duration', 'billsec', \
        'disposition', 'amaflags', 'accountcode', 'uniqueid', 'userfield')

    @classmethod
    def content_length(cls, cdr):
        return len(cdr.content)

    @classmethod
    def resource_uri(cls, cdr):
        return ('cdr', [ 'json', ])

    @throttle(1000, 1*60) # Throttle if more that 1000 times within 1 minute
    def read(self, request, uniqueid=None):
        """
        Read last 10 CDR created, or a specific CDR if uniqueid is supplied
        
        Attributes :
        [uniqueid value]
        
        CURL Testing :
        curl -u username:password -i -H "Accept: application/json" -X GET http://127.0.0.1:8000/cdr/api/cdr/
        curl -u username:password -i -H "Accept: application/json" -X GET http://127.0.0.1:8000/cdr/api/cdr/xx/
        """
        base = CDR.objects
        if uniqueid :
            try :
                list_cdr = base.get(uniqueid=uniqueid)
                return list_cdr
            except :
                return rc.NOT_FOUND
        else:
            return base.all().order_by('-acctid')[:10]

    def create(self, request):
        """
        Create new CDR
        
        Attributes : 
        'src', 'dst', 'calldate', 'clid', 'dcontext', 'channel', \
        'dstchannel', 'lastapp', 'lastdata', 'duration', 'billsec', \
        'disposition', 'amaflags', 'accountcode', 'uniqueid', 'userfield'
        
        CURL Testing :
        curl -u username:password -i -H "Accept: application/json" -X POST http://127.0.0.1:8000/cdr/api/cdr -d "uniqueid=2342jtdsf-00123&calldate=2011-04-16 10:50:11&src=1231321&dcontext=mycontext&dst=650784355&disposition=ANSWERED"
        """
        attrs = self.flatten_dict(request.POST)
        #if self.exists(**attrs):
        #    return rc.DUPLICATE_ENTRY
        #else:
        src = get_attribute(attrs, 'src')
        dst = get_attribute(attrs, 'dst')
        clid = get_attribute(attrs, 'clid')
        dcontext = get_attribute(attrs, 'dcontext')
        channel = get_attribute(attrs, 'channel')
        dstchannel = get_attribute(attrs, 'dstchannel')
        lastapp = get_attribute(attrs, 'lastapp')
        lastdata = get_attribute(attrs, 'lastdata')
        duration = get_attribute(attrs, 'duration')
        billsec = get_attribute(attrs, 'billsec')
        disposition = get_attribute(attrs, 'disposition')
        amaflags = get_attribute(attrs, 'amaflags')
        accountcode = get_attribute(attrs, 'accountcode')
        uniqueid = get_attribute(attrs, 'uniqueid')
        userfield = get_attribute(attrs, 'userfield')
        calldate = get_attribute(attrs, 'calldate')
                                      
        #Validate disposition
        if isint(disposition):
            disposition = int(disposition)
        else:
            disposition = dic_disposition[disposition]
        
        #Validate duration
        if not isint(duration):
            duration = 0
        else:
            duration = int(duration)
        
        #Validate billsec    
        if not isint(billsec):
            billsec = 0
        else:
            billsec = int(billsec)
        
        #Validate amaflags
        if not isint(amaflags):
            amaflags = 0
        else:
            amaflags = int(amaflags)
        
        #Validate calldate
        if calldate is None:
            calldate = str(datetime.now() - timedelta(seconds = duration))
        else:
            calldate = datetime.strptime(calldate, '%Y-%m-%d %H:%M:%S')
        
        #print "(src=%s, dst=%s,clid=%s, dcontext=%s, channel=%s, dstchannel=%s, lastapp=%s, lastdata=%s, duration=%s, billsec=%s, disposition=%s, amaflags=%s, accountcode=%s, uniqueid=%s, userfield=%s, calldate=%s)" % (str(src), str(dst), str(clid), str(dcontext), str(channel), str(dstchannel), str(lastapp), str(lastdata), str(duration), str(billsec), str(disposition), str(amaflags),  str(accountcode),  str(uniqueid),  str(userfield),  str(calldate))
        
        new_cdr = CDR(src=src,
                        dst=dst,
                        clid=clid,
                        dcontext=dcontext,
                        channel=channel,
                        dstchannel=dstchannel,
                        lastapp=lastapp,
                        lastdata=lastdata,
                        duration=duration,
                        billsec=billsec,
                        disposition=disposition,
                        amaflags=amaflags,
                        accountcode=accountcode,
                        uniqueid=uniqueid,
                        userfield=userfield,
                        calldate=calldate)
                        
        new_cdr.save()
        return new_cdr
        return 1
    
    #@throttle(5, 10*60) # allow 5 times in 10 minutes
    def update(self, request, uniqueid):
        """
        Update callrequest
        
        Attributes : 
        duration
        
        CURL Testing :
        curl -u username:password -i -H "Accept: application/json" -X PUT http://127.0.0.1:8000/cdr/api/cdr/%uniqueid%/ -d "duration=55"
        """
        try :
            cdr = CDR.objects.get(uniqueid=uniqueid)
            cdr.duration = request.PUT.get('duration')
            cdr.save()
            return cdr
        except :
            return rc.NOT_HERE
            

