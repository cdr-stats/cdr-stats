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
from django.db import models
from django.utils.translation import gettext as _
from voip_gateway.models import Gateway
from voip_billing.models import VoIPPlan, VoIPRetailRate, VoIPCarrierRate
from country_dialcode.models import Prefix
from uuid import uuid1

VOIPCALL_DISPOSITION = (
    (1, _('ANSWER')),
    (2, _('BUSY')),
    (3, _('NOANSWER')),
    (4, _('CANCEL')),
    (5, _('CONGESTION')),
    (6, _('CHANUNAVAIL')),
    (7, _('DONTCALL')),
    (8, _('TORTURE')),
    (9, _('INVALIDARGS')),
    (20, _('NOROUTE')),
    (30, _('FORBIDDEN')),
)

def str_uuid1():
    return str(uuid1())


class VoIPCall(models.Model):
    """
    VoIP Report

    This gives information of all the calls made with
    the carrier charges and revenue of each call.
    """
    user = models.ForeignKey('auth.User', related_name='Call Sender',)

    callid = models.CharField(max_length=120, help_text=_("VoIP Call-ID"))
    #uniqueid = models.CharField(max_length=90,
    #                           help_text=_("UniqueID from VoIP server"))
    uniqueid = models.CharField(default=str_uuid1(), db_index=True,
        max_length=120, null=True, blank=True,
        help_text=_("UniqueID from VoIP server"))
    callerid = models.CharField(max_length=120, verbose_name=_('CallerID'))
    dnid = models.CharField(max_length=120, verbose_name=_('DNID'))
    recipient_number = models.CharField(max_length=32,
                    help_text=_(u'The international number of the \
                    recipient, without the leading +'), null=True, blank=True)
    nasipaddress = models.CharField(max_length=90)
    
    starting_date = models.DateTimeField(null=True, blank=True, editable=False)
    sessiontime = models.IntegerField(null=True, blank=True)
    sessiontime_real = models.IntegerField(null=True, blank=True)
    
    disposition = models.IntegerField(null=True, blank=True,
                        choices=VOIPCALL_DISPOSITION)
    prefix = models.ForeignKey(Prefix, db_column="prefix",
                               verbose_name=_("Destination"), null=True,
                               blank=True, help_text=_("Select Prefix"))
    billed = models.BooleanField(default=False)
    
    def destination_name(self):
        if self.prefix is None:
            return "0"
        else:
            return "%s - %s" % (self.prefix.destination, self.prefix)
        
    def duration(self):        
        min = int(self.sessiontime_real / 60)
        sec = int(self.sessiontime_real % 60)
        return "%02d" % min + ":" + "%02d" % sec

    class Meta:
        db_table = u'voipcall_cdr'
        app_label = _('voip_report')        

    def _update_voip_call_status(self, voipcall_id):
        voipcall = VoIPCall.objects.get(pk=voipcall_id)
        if voipcall.disposition != 1:
            voipcall.billed = False
        else:
            voipcall.billed = True
        voipcall.save()
        return voipcall


class VoIPCall_Report(VoIPCall):
    """
    VoIP Report

    This gives information of all the calls made with
    the carrier charges and revenue of each call.
    """
    carrier_cost = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    retail_cost = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    carrier_rate = models.ForeignKey(VoIPCarrierRate, related_name="carrie rate",
        null=True, blank=True)
    retail_rate = models.ForeignKey(VoIPRetailRate, related_name="retail rate",
        null=True, blank=True)
    voipplan = models.ForeignKey(VoIPPlan, null=True, blank=True, editable=False)
    gateway = models.ForeignKey(Gateway, null=True, blank=True, editable=False)
    #did = models.ForeignKey(Did, null=True,
    #                            blank=True, editable=False)
                                    
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Date"))
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'voipcall_report'
        app_label = _('voip_report')
        verbose_name = _("VoIP Call Report")
        verbose_name_plural = _("VoIP Call Report")
        permissions = (
            ("daily_billing_report", _('Can view CDR daily billing report')),
            ("hourly_billing_report", _('Can view CDR hourly billing report')),
        )

    def __unicode__(self):
        return "%s [%d] " % (self.id, self.retail_cost)

    def voipplan_name(self):
        return "%s" % (self.voipplan.name)
    voipplan_name.short_description = _('VoIP Plan')

    #def retail_cost(self):
    #    return " %.3f %s" % (self.carriercost, self.user.currency)
    #retail_cost.short_description = _('Retail Cost')

    #def carrier_cost(self):
    #    return " %.3f %s" % (self.retailcost,self.user.currency)
    #carrier_cost.short_description = _('Carrier Cost')
    
    def _bill(self, voipcall_id, voipplan_id):
        """
        Billing of VoIP Call
        """
        from voip_billing.rate_engine import rate_engine
        result_data = rate_engine(voipcall_id, voipplan_id)
        return result_data
