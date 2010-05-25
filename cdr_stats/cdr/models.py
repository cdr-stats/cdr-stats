from django.db import models
from django.db.models import permalink

class CDR(models.Model):
    acctid = models.PositiveIntegerField(primary_key=True, db_column = 'acctid')
    src = models.CharField(max_length=80)
    dst = models.CharField(max_length=80)
    calldate = models.DateTimeField()
    clid = models.CharField(max_length=80)
    dcontext = models.CharField(max_length=80)
    channel = models.CharField(max_length=80)
    dstchannel = models.CharField(max_length=80)
    lastapp = models.CharField(max_length=80)
    lastdata = models.CharField(max_length=80)
    duration = models.PositiveIntegerField()
    billsec = models.PositiveIntegerField()
    disposition = models.PositiveIntegerField()
    amaflags = models.PositiveIntegerField()
    accountcode = models.PositiveIntegerField()
    uniqueid = models.CharField(max_length=32)
    userfield = models.CharField(max_length=80)
    test = models.CharField(max_length=80)

    class Meta:
        db_table = 'cdr'
        # Only in trunk 1.1 managed = False     # The database is normally already created

    def __unicode__(self):
        return "%s -> %s" % (self.src,self.dst)

    def get_list(self):
        return [(self.acctid, self.src, self.dst, self.calldate, self.clid, self.dcontext, self.channel, self.dstchannel, self.lastapp, self.lastdata, self.duration, self.billsec, self.disposition, self.amaflags, self.accountcode, self.uniqueid, self.userfield, self.test)]
    
    @permalink
    def get_absolute_url(self):
        return ('cdr_detail', [str(self.acctid)])
        
    class Dilla:
        skip_model = False
    	field_extras={ #field extras are for defining custom dilla behavior per field
		#	'email':{
		#		'generator':'generate_EmailField', #can point to a callable, which must return the desired value. If this is a string, it looks for a method in the dilla.py file.
		#	},
		    'acctid':{
		        'integer_range':(1, 2147483647)
		    },
			'src':{
				'generator':None, #can point to a callable, which must return the desired value. If this is a string, it looks for a method in the dilla.py file.
				'generator_wants_extras':False, #whether or not to pass this "field extra" hash item to the callable
				'spaces':False, #if Char/TextField, whether or not to allow spaces
				'word_count':1, #if Char/TextField, the number of words to generate
			},
			'dst':{
				'generator':None, #can point to a callable, which must return the desired value. If this is a string, it looks for a method in the dilla.py file.
				'generator_wants_extras':False, #whether or not to pass this "field extra" hash item to the callable
				'spaces':False, #if Char/TextField, whether or not to allow spaces
				'word_count':1, #if Char/TextField, the number of words to generate
			},
		}



