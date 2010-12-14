from django.db import models
from django.db.models import permalink
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.auth.models import User



DISPOSITION = (
    (1, _('ANSWER')),
    (2, _('BUSY')),
    (3, _('NOANSWER')),
    (4, _('CANCEL')),
    (5, _('CONGESTION')),
    (6, _('CHANUNAVAIL')),
    (7, _('DONTCALL')),
    (8, _('TORTURE')),
    (9, _('INVALIDARGS')),
    (10,_('ERROR'))
)
dic_disposition = {'ANSWER': '1', 'ANSWERED': '1', 'BUSY': '2', 'NOANSWER': '3', 'NO ANSWER': '3', 'CANCEL': '4', 'CONGESTION': '5', 'CHANUNAVAIL': '6', 'DONTCALL': '7', 'TORTURE': '8', 'INVALIDARGS': '9'}

AMAFLAGS = (
    (1,'BILLING'),
    (2,'DOCUMENTATION'),
    (3,'IGNORE'),
    (4,'ERROR')
)
dic_amaflags = {'BILLING':1, 'DOCUMENTATION':2, 'IGNORE':3, 'ERROR':4 }


class Company(models.Model):
    name = models.CharField(max_length=50, blank=False, null=True)
    address = models.TextField(max_length=400, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    fax = models.CharField(max_length=30, blank=True, null=True)
    
    def __unicode__(self):
        return '[%s] %s' %(self.id, self.name)
        
    class Meta:
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")
        #app_label = "Company"
        db_table = "cdr_company"
        
    class Dilla:
        skip_model = True        

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    accountcode = models.PositiveIntegerField(null=True, blank=True)
    company = models.OneToOneField(Company, verbose_name='Company', null=True, blank=True)
    
    class Dilla:
        skip_model = True
        
    class Meta:
        db_table = "cdr_userprofile"


class Customer(User):    
    class Meta:
        proxy = True
        #app_label = 'auth'
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'

class Staff(User):
    class Meta:
        proxy = True
        #app_label = 'auth'
        verbose_name = 'Admin'
        verbose_name_plural = 'Admins'
        
    def save(self, **kwargs):
        if not self.pk:
            self.is_staff = 1
            self.is_superuser = 1
        super(Staff, self).save(**kwargs)


class Classification(models.Model):
    """ Defines the call types used in ratetables and cost rates"""
    name = models.CharField(max_length=120, unique=True)
    regex = models.CharField(max_length=255, unique=True, help_text='Regex used to match the telephone number dialled')
    channel = models.CharField(max_length=120, unique=False, null=True, default='DAHDI', help_text='Name of the channel to find calls on, leave blank for all channels')

    def __unicode__(self):
        return u"{0} {1}".format(self.name, self.regex)

class RateTable(models.Model):
    """ Rate table associated to an account code to determine the call costs in order to bill the client"""
    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=255)

    def __unicode__(self):
        return u"{0} {1}".format(self.name, self.description)


class Rate(models.Model):
    """ individual call type (Clasification) costs for the associated rate table"""
    ratetable = models.ForeignKey(RateTable)
    classification = models.ForeignKey(Classification)
    flagfall = models.DecimalField(max_digits=6, decimal_places=5,default=0)
    interval = models.PositiveIntegerField(default=0, help_text='call cost = flagfall + (call duration / interval) * rate')
    firstrate = models.DecimalField(max_digits=6, decimal_places=5,default=0, help_text='cost of the first rate, ie $0.01')
    remainingrate = models.DecimalField(max_digits=6, decimal_places=5,default=0, help_text='call rate cost for ever interval exculding the first one. usually same rate as firstrate')
    
    def __unicode__(self):
        return u"{0} : {1}".format(self.ratetable.name, self.classification.name)
    
    class META:
        unique_together = ("ratetable", "classification")

class CostRateTable(models.Model):
    """ defines the cost of the call for internal reporting purposes"""
    classification = models.ForeignKey(Classification, unique=True)
    flagfall = models.DecimalField(max_digits=6, decimal_places=5,default=0)
    interval = models.PositiveIntegerField(default=0, help_text='call cost = flagfall + (call duration / interval) * rate')
    firstrate = models.DecimalField(max_digits=6, decimal_places=5,default=0, help_text='cost of the first rate, ie $0.01')
    remainingrate = models.DecimalField(max_digits=6, decimal_places=5,default=0, help_text='call rate cost for ever interval exculding the first one. usually same rate as firstrate')
    
    def __unicode__(self):
        return u"{0}".format(self.classification.name)
    
class AccountCode(models.Model):
    """ Calls need to have an account code assigned to them to determin who the call should be billed to """
    accountcode = models.CharField(max_length=80, blank=False, unique=True)
    description = models.CharField(max_length=80, blank=False)
    company = models.ForeignKey(Company, blank=True, null=True)
    ratetable = models.ForeignKey(RateTable, blank=True, null=True)

    def __unicode__(self):
        return u"{0} {1}".format(self.accountcode, self.description)

class Invoice(models.Model):
    """ clients invoice """
    start = models.DateTimeField()
    end = models.DateTimeField()
    company = models.ForeignKey(Company)

    def __unicode__(self):
        return u"{0} from {1} to {2}".format(self.company, self.start, self.end)

class CDR(models.Model):
    """ CDR data, raw extract from asterisk"""
    accountcode = models.ForeignKey(AccountCode)
    src = models.CharField(max_length=80, blank=True)
    dst = models.CharField(max_length=80, blank=True)
    dcontext = models.CharField(max_length=80, blank=True)
    clid = models.CharField(max_length=80, blank=True)
    channel = models.CharField(max_length=80, blank=True)
    dstchannel = models.CharField(max_length=80, blank=True)
    lastapp = models.CharField(max_length=80, blank=True)
    lastdata = models.CharField(max_length=80, blank=True)
    start = models.DateTimeField()
    answered = models.DateTimeField(null=True)
    end = models.DateTimeField()
    duration = models.PositiveIntegerField(default=0)
    billsec = models.PositiveIntegerField(default=0)
    disposition = models.PositiveIntegerField(choices=DISPOSITION, default=10)
    amaflags = models.PositiveIntegerField(choices=AMAFLAGS, default=4)
    userfield = models.CharField(max_length=255, blank=True)
    uniqueid = models.CharField(max_length=32, blank=True)
    
    class Meta:
        db_table = getattr(settings, 'CDR_TABLE_NAME', 'cdr' )
        # Only in trunk 1.1 managed = False     # The database is normally already created
        verbose_name = _("CDR")
        verbose_name_plural = _("CDR's")
        #app_label = "Call Detail Records"

    def __unicode__(self):
        return "%s -> %s" % (self.src,self.dst)
    
    def get_list(self):
        return [(self.id, self.src, self.dst, self.start, self.clid, self.dcontext, self.channel, self.dstchannel, self.lastapp, self.lastdata, self.duration, self.billsec, self.get_disposition_display(), self.amaflags, self.accountcode.name, self.uniqueid, self.userfield)]
    
    @permalink
    def get_absolute_url(self):
        return ('cdr_detail', [str(self.id)])
        
    class Dilla:
        skip_model = False
    	field_extras={ #field extras are for defining custom dilla behavior per field
		#	'email':{
		#		'generator':'generate_EmailField', #can point to a callable, which must return the desired value. If this is a string, it looks for a method in the dilla.py file.
		#	},
		    'accountcode':{
		        'integer_range':(10000, 99999)
		    },
		    'disposition':{
		        'integer_range':(1, 9)
		    },
			'src':{
				'generator':'phonenumber'
			},
			'dst':{
				'generator':'phonenumber'
			},
			'clid':{
				'generator':'phonenumber'
			},
			'channel':{
				'generator':'sip_URI'
			},
			'start':{
				'day_delta': 10, #The day delta to generate the date, minus today
				'hour_delta': 24, #The day delta to generate the date, minus the current hour
			},
		}

class InvoiceDetail(models.Model):
    """ cost of each call for an invoice """
    call = models.ForeignKey(CDR)
    invoice = models.ForeignKey(Invoice)
    classification = models.ForeignKey(Classification)
    cost = models.DecimalField(max_digits=8, decimal_places=5,default=0, help_text = 'Internal cost from the telco')
    bill = models.DecimalField(max_digits=8, decimal_places=5,default=0, help_text = 'Cost to charge the client')
    
    def __unicode__(self):
        return u"Invoice: {0} classification: {1} Bill:{2}".format(self.invoice, self.classification.name, self.bill)
    


