#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2015 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from postgres.fields import json_field
from django_lets_go.utils import Choice
from switch.models import Switch
from country_dialcode.models import Prefix
from country_dialcode.models import Country
# from localflavor.us.models import USStateField
from cache_utils.decorators import cached
import caching.base
import random
from uuid import uuid1
import datetime
import time
import string

random.seed()


# list of exit code : http://www.howtocallabroad.com/codes.html
COUNTRY_PREFIX = ['0034', '011346', '+3465',  # Spain
                  '3912', '39', '+3928',  # Italy
                  '15', '17',  # US
                  '16', '1640',  # Canada
                  '44', '441', '00442',  # UK
                  '45', '451', '00452',  # Denmark
                  '32', '321', '0322',  # Belgium
                  '91', '919', '0911',  # India
                  '53', '531', '00532',  # Cuba
                  '55', '551', '552',  # Brazil
                  ]


class CDR_SOURCE_TYPE(Choice):

    """
    List of call source type
    """
    UNKNOWN = 0, _('UNKNOWN')
    CSV = 1, _('CSV UPLOAD')
    API = 2, _('API')
    FREESWITCH = 3, _('FREESWITCH')
    ASTERISK = 4, _('ASTERISK')
    YATE = 5, _('YATE')
    KAMAILIO = 6, _('KAMAILIO')
    OPENSIPS = 7, _('OPENSIPS')
    SIPWISE = 8, _('SIPWISE')
    VERAZ = 9, _('VERAZ')
    # change also switch.models.SWITCH_TYPE


class CALL_DIRECTION(Choice):

    """
    List of call direction
    """
    NOTDEFINED = 0, _('NOT DEFINED')
    INBOUND = 1, _('INBOUND')
    OUTBOUND = 2, _('OUTBOUND')


class HangupCauseManager(models.Manager):

    """HangupCause Manager"""

    @cached(3600)
    def get_all_hangupcause(self):
        result = []
        for l in HangupCause.objects.all():
            if len(l.enumeration) > 0:
                result.append((l.id, l.enumeration))
            else:
                result.append((l.id, l.cause[:25].upper() + '...'))
        return result


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
    objects = HangupCauseManager()

    def __unicode__(self):
        return '[%s] %s' % (self.code, self.enumeration)

    def listall(self):
        result = []
        for l in self.objects.all():
            if len(l.enumeration) > 0:
                result.append((l.id, l.enumeration))
            else:
                result.append((l.id, l.cause[:25].upper() + '...'))
        return result

    class Meta:
        verbose_name = _("hangup cause")
        verbose_name_plural = _("hangup causes")
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
    user = models.ForeignKey(User, related_name="Call Owner")
    switch = models.ForeignKey(Switch, verbose_name=_("Switch"), null=False)
    cdr_source_type = models.IntegerField(choices=CDR_SOURCE_TYPE, default=CDR_SOURCE_TYPE.FREESWITCH,
                                          null=True, blank=True)
    # CID & Destination
    callid = models.CharField(max_length=80, help_text=_("VoIP call-ID"))
    caller_id_number = models.CharField(max_length=80, verbose_name=_("CallerID Number"), blank=True)
    caller_id_name = models.CharField(max_length=80, verbose_name=_("CallerID Name"), blank=True)
    destination_number = models.CharField(max_length=80, verbose_name=_("destination number"),
                                          help_text=_("the international number of the recipient, without the leading +"),
                                          db_index=True)
    dialcode = models.ForeignKey(Prefix, verbose_name=_("dialcode"), null=True, blank=True)
    state = models.CharField(max_length=5, verbose_name=_("State/Region"), null=True, blank=True)
    channel = models.CharField(max_length=80, verbose_name=_("channel"), null=True, blank=True)

    # Date & Duration
    starting_date = models.DateTimeField(verbose_name=_("starting date"), db_index=True)
    duration = models.IntegerField(default=0, verbose_name=_("duration"))
    billsec = models.IntegerField(default=0, verbose_name=_("bill sec"))
    progresssec = models.IntegerField(default=0, null=True, blank=True, verbose_name=_("progress sec"))
    answersec = models.IntegerField(default=0, null=True, blank=True, verbose_name=_("answer sec"))
    waitsec = models.IntegerField(default=0, null=True, blank=True, verbose_name=_("wait sec"))

    # Disposition
    hangup_cause = models.ForeignKey(HangupCause, verbose_name=_("hangup cause"),
                                     null=False, blank=False)
    direction = models.IntegerField(choices=CALL_DIRECTION, null=False, blank=False,
                                    default=CALL_DIRECTION.INBOUND, verbose_name=_("direction"),
                                    db_index=True)
    country = models.ForeignKey(Country, null=True, blank=True, verbose_name=_("country"))
    authorized = models.BooleanField(default=False, verbose_name=_("authorized"))

    # Billing
    accountcode = models.CharField(max_length=80, verbose_name=_("account code"), blank=True)
    buy_rate = models.DecimalField(default=0, verbose_name=_("Buy Rate"),
                                   max_digits=10, decimal_places=5)
    buy_cost = models.DecimalField(default=0, verbose_name=_("Buy Cost"),
                                   max_digits=12, decimal_places=5)
    sell_rate = models.DecimalField(default=0, verbose_name=_("Sell Rate"),
                                    max_digits=10, decimal_places=5)
    sell_cost = models.DecimalField(default=0, verbose_name=_("Sell Cost"),
                                    max_digits=12, decimal_places=5)

    # Postgresql >= 9.4 Json field
    data = json_field.JSONField()

    class Meta:
        db_table = 'voip_cdr'
        verbose_name = _("Call")
        verbose_name_plural = _("Calls")

    def __unicode__(self):
        return u"id:%d - dst:%s - %s" % (self.id, self.destination_number, str(self.starting_date)[0:16])

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

    @classmethod
    def generate_fake_cdr(cls, day_delta_int):
        """return tuples of fake CDR data"""

        # HANGUP_CAUSE = ['NORMAL_CLEARING', 'USER_BUSY', 'NO_ANSWER', 'CALL_REJECTED', 'INVALID_NUMBER_FORMAT']
        # HANGUP_CAUSE_Q850 = ['16', '17', '19', '21', '28']
        """
        HANGUP_CAUSE = ['NORMAL_CLEARING', 'USER_BUSY', 'NO_ANSWER']
        HANGUP_CAUSE_Q850 = ['16', '17', '19']

        rand_hangup = random.randint(0, len(HANGUP_CAUSE)-1)
        hangup_cause = HANGUP_CAUSE[rand_hangup]
        hangup_cause_q850 = HANGUP_CAUSE_Q850[rand_hangup]
        if hangup_cause == 'NORMAL_CLEARING':
            duration = random.randint(1, 200)
            billsec = random.randint(1, 200)
        else:
            duration = 0
            billsec = 0
        """
        # from django.db.models import Q
        # import operator
        # predicates = [
        #     ('code__exact', 16), ('code__exact', 17), ('code__exact', 18)
        # ]
        # q_list = [Q(x) for x in predicates]
        # list_hg = HangupCause.objects.filter(reduce(operator.or_, q_list))

        HANGUP_CAUSE_Q850 = [16, 17, 19]
        list_hg = HangupCause.objects.filter(code__in=HANGUP_CAUSE_Q850)
        hangupcause = list_hg[random.randint(0, len(list_hg) - 1)]
        if hangupcause.code != 16:
            # Increase chances to have Answered calls
            hangupcause = list_hg[random.randint(0, len(list_hg) - 1)]
        hangup_cause_q850 = hangupcause.code
        if hangupcause.code == 16:
            duration = random.randint(1, 200)
            billsec = random.randint(1, 200)
        else:
            duration = 0
            billsec = 0

        delta_days = random.randint(0, day_delta_int)
        delta_minutes = random.randint(1, 1440)

        answer_stamp = datetime.datetime.now() \
            - datetime.timedelta(minutes=delta_minutes) \
            - datetime.timedelta(days=delta_days)

        # convert answer_stamp into milliseconds
        start_uepoch = int(time.mktime(answer_stamp.timetuple()))

        caller_id = ''.join([random.choice(string.digits) for i in range(8)])
        channel_name = 'sofia/internal/' + caller_id + '@127.0.0.1'
        destination_number = ''.join([random.choice(string.digits) for i in range(8)])

        if random.randint(1, 20) == 1:
            # Add local calls
            dialcode = None
            country_id = None
            authorized = 1
            destination_number = ''.join([random.choice(string.digits) for i in range(5)])
        else:
            # International calls
            destination_number = random.choice(COUNTRY_PREFIX) + destination_number

            from cdr_alert.functions_blacklist import verify_auth_dest_number
            destination_data = verify_auth_dest_number(destination_number)
            authorized = destination_data['authorized']
            country_id = destination_data['country_id']
            dialcode = destination_data['prefix_id']

        end_stamp = str(datetime.datetime.now()
                        - datetime.timedelta(minutes=delta_minutes)
                        - datetime.timedelta(days=delta_days)
                        + datetime.timedelta(seconds=duration))
        callid = str(uuid1())

        cdr_source_type = CDR_SOURCE_TYPE.FREESWITCH
        direction = CALL_DIRECTION.INBOUND

        return (
            callid, answer_stamp, start_uepoch, caller_id,
            channel_name, destination_number, dialcode, hangupcause,
            hangup_cause_q850, duration, billsec, end_stamp,
            cdr_source_type, authorized, country_id, direction,
            # accountcode, buy_rate, buy_cost, sell_rate, sell_cost
        )
