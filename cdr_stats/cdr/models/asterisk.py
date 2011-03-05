from django.db import models
from django.db.models import *
from django.utils.translation import gettext_lazy as _
from django.conf import settings

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
)

dic_disposition = {'ANSWER': '1', 'ANSWERED': '1', 'BUSY': '2', 'NOANSWER': '3', 'NO ANSWER': '3', 'CANCEL': '4', 'FAILED': '4', 'CONGESTION': '5', 'CHANUNAVAIL': '6', 'DONTCALL': '7', 'TORTURE': '8', 'INVALIDARGS': '9'}


class AsteriskCDR(models.Model):
    #acctid = models.PositiveIntegerField(primary_key=True, db_column = 'acctid')
    src = models.CharField(max_length=80, blank=True)
    dst = models.CharField(max_length=80, blank=True)
    calldate = models.DateTimeField()
    clid = models.CharField(max_length=80, blank=True)
    dcontext = models.CharField(max_length=80, blank=True)
    channel = models.CharField(max_length=80, blank=True)
    dstchannel = models.CharField(max_length=80, blank=True)
    lastapp = models.CharField(max_length=80, blank=True)
    lastdata = models.CharField(max_length=80, blank=True)
    duration = models.PositiveIntegerField(default=0)
    billsec = models.PositiveIntegerField(default=0)
    disposition = models.PositiveIntegerField(choices=DISPOSITION, default=1)
    amaflags = models.PositiveIntegerField(null=True)
    accountcode = models.PositiveIntegerField(default=0)
    uniqueid = models.CharField(max_length=32, blank=True)
    userfield = models.CharField(max_length=80, blank=True)
    #test = models.CharField(max_length=80, blank=True)
    
    class Meta:
        db_table = getattr(settings, 'ASTERISK_CDR_TABLE_NAME', 'cdr' )
        # Only in trunk 1.1 managed = False     # The database is normally already created
        verbose_name = _("CDR")
        verbose_name_plural = _("CDR's")
        app_label = "cdr"

    def __unicode__(self):
        return "%s -> %s" % (self.src,self.dst)
    
    def get_list(self):
        return [(self.id, self.src, self.dst, self.calldate, self.clid, self.dcontext, self.channel, self.dstchannel, self.lastapp, self.lastdata, self.duration, self.billsec, self.get_disposition_display(), self.amaflags, self.accountcode, self.uniqueid, self.userfield, self.test)]
    
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
			'calldate':{
				'day_delta': 10, #The day delta to generate the date, minus today
				'hour_delta': 24, #The day delta to generate the date, minus the current hour
			},
		}



