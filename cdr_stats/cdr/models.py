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
)
dic_disposition = {'ANSWER': '1', 'ANSWERED': '1', 'BUSY': '2', 'NOANSWER': '3', 'NO ANSWER': '3', 'CANCEL': '4', 'FAILED': '4', 'CONGESTION': '5', 'CHANUNAVAIL': '6', 'DONTCALL': '7', 'TORTURE': '8', 'INVALIDARGS': '9'}


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
         

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    accountcode = models.PositiveIntegerField(null=True, blank=True)
    company = models.OneToOneField(Company, verbose_name='Company', null=True, blank=True)
        
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


class CDR(models.Model):
    table_fields = settings.CDR_TABLE_FIELDS
    #FreePBX is adding a acctid to the Asterisk table
    #it's a good practice to have an id
    acctid = models.AutoField(primary_key=True, db_column = table_fields['acctid'])
    src = models.CharField(max_length=80, blank=True, null=True, db_column = table_fields['src'])
    dst = models.CharField(max_length=80, blank=True, null=True, db_column = table_fields['dst'])
    calldate = models.DateTimeField(db_column = table_fields['calldate'])
    clid = models.CharField(max_length=80, blank=True, null=True, db_column = table_fields['clid'])
    dcontext = models.CharField(max_length=80, blank=True, null=True, db_column = table_fields['dcontext'])
    channel = models.CharField(max_length=80, blank=True, null=True, db_column = table_fields['channel'])
    dstchannel = models.CharField(max_length=80, blank=True, null=True, db_column = table_fields['dstchannel'])
    lastapp = models.CharField(max_length=80, blank=True, null=True, db_column = table_fields['lastapp'])
    lastdata = models.CharField(max_length=80, blank=True, null=True, db_column = table_fields['lastdata'])
    duration = models.PositiveIntegerField(default=0, null=True, db_column = table_fields['duration'])
    billsec = models.PositiveIntegerField(default=0, null=True, db_column = table_fields['billsec'])
    disposition = models.PositiveIntegerField(choices=DISPOSITION, default=1, db_column = table_fields['disposition'])
    amaflags = models.PositiveIntegerField(default=0, null=True, db_column = table_fields['amaflags'])
    accountcode = models.PositiveIntegerField(default=0, null=True, db_column = table_fields['accountcode'])
    uniqueid = models.CharField(max_length=32, blank=True, null=True, db_column = table_fields['uniqueid'])
    userfield = models.CharField(max_length=80, blank=True, null=True, db_column = table_fields['userfield'])
    
    class Meta:
        db_table = getattr(settings, 'CDR_TABLE_NAME', 'cdr' )
        # Only in trunk 1.1 managed = False     # The database is normally already created
        verbose_name = _("CDR")
        verbose_name_plural = _("CDR's")
        #app_label = "Call Detail Records"

    def __unicode__(self):
        return "%s -> %s" % (self.src,self.dst)
    
    def get_list(self):
        return [(self.id, self.src, self.dst, self.calldate, self.clid, self.dcontext, self.channel, self.dstchannel, self.lastapp, self.lastdata, self.duration, self.billsec, self.get_disposition_display(), self.amaflags, self.accountcode, self.uniqueid, self.userfield, self.test)]
    
    @permalink
    def get_absolute_url(self):
        return ('cdr_detail', [str(self.id)])
    


