#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2013 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import UUIDField
from django_lets_go.utils import Choice
from country_dialcode.models import Prefix
from country_dialcode.models import Country
from localflavor.us.models import USStateField
import caching.base


class CDR_SOURCE_TYPE(Choice):
    """
    List of call source type
    """
    CSV = 1, _('CSV UPLOAD')
    API = 2, _('API')
    ASTERISK = 3, _('ASTERISK')
    FREESWITCH = 4, _('FREESWITCH')
    KAMAILIO = 5, _('KAMAILIO')
    YATE = 6, _('YATE')
    OPENSIPS = 7, _('OPENSIPS')


class CALL_DIRECTION(Choice):
    """
    List of call direction
    """
    NOTDEFINED = 0, _('NOT DEFINED')
    INBOUND = 1, _('INBOUND')
    OUTBOUND = 2, _('OUTBOUND')


class CALL_DISPOSITION(Choice):
    """
    List of call disposition
    """
    ANSWER = 1, _('ANSWER')
    BUSY = 2, _('BUSY')
    NOANSWER = 3, _('NOANSWER')
    CANCEL = 4, _('CANCEL')
    CONGESTION = 5, _('CONGESTION')
    FAILED = 6, _('FAILED')  # Added to catch all errors


#Asterisk disposition
#TODO: Delete this?
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


#todo: remove first 2 elements from CDR_SOURCE_TYPE
class SWITCH_TYPE(Choice):
    """
    List of switches
    """
    ASTERISK = 3, _('ASTERISK')
    FREESWITCH = 4, _('FREESWITCH')
    KAMAILIO = 5, _('KAMAILIO')
    YATE = 6, _('YATE')
    OPENSIPS = 7, _('OPENSIPS')


class Switch(caching.base.CachingMixin, models.Model):
    """This defines the Switch

    **Attributes**:

        * ``name`` - Name of switch.
        * ``ipaddress`` - ipaddress

    **Name of DB table**: voip_switch
    """
    name = models.CharField(max_length=100, blank=False,
                            null=True, unique=True)
    ipaddress = models.CharField(max_length=100, blank=False,
                            null=False, unique=True)
    switch_type = models.IntegerField(choices=SWITCH_TYPE, default=SWITCH_TYPE.FREESWITCH,
                                      max_length=100, null=False)
    key_uuid = UUIDField(auto=True)

    objects = caching.base.CachingManager()

    def __unicode__(self):
        return '[%s] %s' % (self.id, self.ipaddress)

    class Meta:
        verbose_name = _("switch")
        verbose_name_plural = _("switches")
        db_table = "voip_switch"


class AccountCode(caching.base.CachingMixin, models.Model):
    """This defines the Accountcode

    **Attributes**:

        * ``name`` - Name of switch.
        * ``ipaddress`` - ipaddress

    **Name of DB table**: voip_switch
    """
    accountcode = models.CharField(max_length=100, blank=False,
                            null=True, unique=True)
    description = models.CharField(max_length=100, blank=False,
                            null=False, unique=True)
    objects = caching.base.CachingManager()

    def __unicode__(self):
        return '[%s] %s' % (self.id, self.accountcode)

    class Meta:
        verbose_name = _("accountcode")
        verbose_name_plural = _("accountcodes")
        db_table = "voip_accountcode"


class HangupCause(caching.base.CachingMixin, models.Model):
    """This defines the HangupCause

    **Attributes**:

        * ``code`` - ITU-T Q.850 Code.
        * ``enumeration`` - Enumeration
        * ``cause`` - cause
        * ``description`` - cause description

    **Name of DB table**: hangup_cause
    """
    code = models.PositiveIntegerField(unique=True, verbose_name=_('code'),
                                       help_text=_("ITU-T Q.850 Code"))
    enumeration = models.CharField(max_length=100, null=True, blank=True,
                                   verbose_name=_('enumeration'))
    cause = models.CharField(max_length=100, null=True, blank=True,
                             verbose_name=_('cause'))
    description = models.TextField(null=True, blank=True,
                                   verbose_name=_('description'))

    def __unicode__(self):
        return '[%s] %s' % (self.code, self.enumeration)

    class Meta:
        verbose_name = _("hangupcause")
        verbose_name_plural = _("hangupcauses")
        db_table = "hangup_cause"


class CDR(models.Model):
    """Call Detail Records give all information on calls made on a softswitch,
    information collected are such like destination number, callerid, duration of the
    call, date and time of the call, disposition of the calls and much more.

    **Attributes**:

        * ``callid`` - Callid of the phonecall
        * ``cdr_source_type`` - Source type of the CDRs
        * ``caller_id_number`` - Caller ID Number
        * ``caller_id_name`` - Caller ID Name
        * ``phone_number`` - Phone number contacted
        * ``dialcode`` - Dialcode of the phonenumber
        * ``starting_date`` - Starting date of the call
        * ``duration`` - Duration of the call
        * ``billsec`` - Billable duration of the call
        * ``progresssec`` -
        * ``answersec`` -
        * ``waitsec`` -
        * ``disposition`` - Disposition of the call
        * ``hangup_cause`` -
        * ``hangup_cause_q850`` -

    **Relationships**:

        * ``user`` - Foreign key relationship to the User model.
        * ``switch_id`` - Foreign key relationship to Switch

    """
    user = models.ForeignKey('auth.User', related_name='Call Owner')
    switch = models.ForeignKey(Switch, verbose_name=_("Switch"), null=False)
    cdr_source_type = models.IntegerField(choices=CDR_SOURCE_TYPE, default=CDR_SOURCE_TYPE.FREESWITCH,
                                          null=True, blank=True)
    # CID & Destination
    callid = models.CharField(max_length=80, help_text=_("VoIP call-ID"))
    caller_id_number = models.CharField(max_length=80, verbose_name=_('CallerID Number'), blank=True)
    caller_id_name = models.CharField(max_length=80, verbose_name=_('CallerID Name'), blank=True)
    destination_number = models.CharField(max_length=80, verbose_name=_("destination number"),
        help_text=_("the international number of the recipient, without the leading +"),
        db_index=True)
    dialcode = models.ForeignKey(Prefix, verbose_name=_("dialcode"), null=True, blank=True)
    state = models.CharField(max_length=5, verbose_name=_('State/Region'), null=True, blank=True)
    channel = models.CharField(max_length=80, verbose_name=_("channel"), null=True, blank=True)

    #Date & Duration
    starting_date = models.DateTimeField(auto_now_add=True, verbose_name=_("starting date"),
                                         db_index=True)
    duration = models.IntegerField(default=0, verbose_name=_("duration"))
    billsec = models.IntegerField(default=0, verbose_name=_("bill sec"))
    progresssec = models.IntegerField(default=0, null=True, blank=True, verbose_name=_("progress sec"))
    answersec = models.IntegerField(default=0, null=True, blank=True, verbose_name=_("answer sec"))
    waitsec = models.IntegerField(default=0, null=True, blank=True, verbose_name=_("wait sec"))

    #TODO: review if this is not duplicate with hangup cause
    # disposition = models.IntegerField(choices=CALL_DISPOSITION, null=False, blank=False,
    #                                   verbose_name=_("disposition"))
    # hangup_cause = models.CharField(max_length=40, null=True, blank=True,
    #                                 verbose_name=_("hangup cause"))
    # hangup_cause_q850 = models.CharField(max_length=10, null=True, blank=True)

    #Disposition / States
    hangup_cause = models.ForeignKey(HangupCause, verbose_name=_("hangup cause"),
                                     null=False, blank=False)
    direction = models.IntegerField(choices=CALL_DIRECTION, null=False, blank=False,
                                    default=CALL_DIRECTION.INBOUND, verbose_name=_("direction"),
                                    db_index=True)
    country = models.ForeignKey(Country, null=True, blank=True, verbose_name=_("country"))
    authorized = models.BooleanField(default=False, verbose_name=_('authorized'))

    #Billing
    accountcode = models.ForeignKey(AccountCode, verbose_name=_("account code"),
                                    null=True, blank=True)
    buy_rate = models.DecimalField(default=0, verbose_name=_("Buy Rate"),
                                   max_digits=10, decimal_places=5)
    buy_cost = models.DecimalField(default=0, verbose_name=_("Buy Cost"),
                                   max_digits=12, decimal_places=5)
    sell_rate = models.DecimalField(default=0, verbose_name=_("Sell Rate"),
                                    max_digits=10, decimal_places=5)
    sell_cost = models.DecimalField(default=0, verbose_name=_("Sell Cost"),
                                    max_digits=12, decimal_places=5)

    def destination_name(self):
        """Return Recipient dialcode"""
        if self.dialcode is None:
            return "0"
        else:
            return self.dialcode.name

    def min_duration(self):
        """Return duration in min & sec"""
        if self.duration:
            min = int(self.duration / 60)
            sec = int(self.duration % 60)
            return "%02d:%02d" % (min, sec)
        else:
            return "00:00"

    class Meta:
        db_table = 'voip_cdr'
        verbose_name = _("VoIP call")
        verbose_name_plural = _("VoIP calls")

    def __unicode__(self):
        return u"id:%d - dst:%s - %s" % (self.id, self.destination_number, str(self.starting_date)[0:16])
