#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2014 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from django.db import models
from django.utils.translation import gettext_lazy as _
from country_dialcode.models import Country
from cdr_alert.constants import PERIOD, STATUS, ALARM_TYPE, \
    ALERT_CONDITION, ALERT_CONDITION_ADD_ON, ALARM_REPROT_STATUS


class AlertRemovePrefix(models.Model):
    """This defines the Alert Remove Prefix
    Define the list of prefixes that need to be removed from the dialed digits,
    assuming the phone numbers are in the format 5559004432, with the signifcant digits
    9004432, the prefix 555 needs to be removed to analyse the phone numbers.

    **Attributes**:

        * ``label`` - Label for the custom prefix
        * ``prefix`` - Prefix value

    **Name of DB table**: alarm
    """
    label = models.CharField(max_length=100, verbose_name=_('label'))
    prefix = models.CharField(max_length=100, unique=True, verbose_name=_('prefix'))
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=_('date'))
    updated_date = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s' % (self.label)

    class Meta:
        verbose_name = _("alert remove prefix")
        verbose_name_plural = _("alert remove prefixes")
        db_table = "alert_remove_prefix"


class Alarm(models.Model):
    """This defines the Alarm

    **Attributes**:

        * ``user`` -
        * ``name`` - Alarm name
        * ``period`` - Day | Week | Month
        * ``type`` - ALOC (average length of call) ; ASR (answer seize ratio)
        * ``alert_condition`` -
        * ``alert_value`` - Input the value for the alert
        * ``alert_condition_add_on`` -
        * ``status`` - Inactive | Active
        * ``email_to_send_alarm`` - email_to

    **Name of DB table**: alert
    """
    user = models.ForeignKey('auth.User', related_name='Alarm_owner')
    name = models.CharField(max_length=100, verbose_name=_('name'))
    period = models.PositiveIntegerField(choices=list(PERIOD), default=PERIOD.DAY, verbose_name=_('period'),
                                         help_text=_('interval to apply alarm'))
    type = models.PositiveIntegerField(choices=list(ALARM_TYPE), default=ALARM_TYPE.ALOC, verbose_name=_('type'),
                                       help_text=_('ALOC (average length of call) ; ASR (answer seize ratio) ; CIC (Consecutive Incomplete Calls) '))
    alert_condition = models.PositiveIntegerField(choices=list(ALERT_CONDITION), verbose_name=_('condition'),
                                                  default=ALERT_CONDITION.IS_LESS_THAN)
    alert_value = models.DecimalField(verbose_name=_('value'), max_digits=5, decimal_places=2,
                                      blank=True, null=True, help_text=_('input the value for the alert'))
    alert_condition_add_on = models.PositiveIntegerField(choices=list(ALERT_CONDITION_ADD_ON),
                                                         default=ALERT_CONDITION_ADD_ON.SAME_DAY)
    status = models.PositiveIntegerField(choices=list(STATUS), default=1, verbose_name=_('status'))
    email_to_send_alarm = models.EmailField(max_length=100, verbose_name=_('email to send alarm'))
    created_date = models.DateTimeField(auto_now_add=True, verbose_name=_('date'))
    updated_date = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s' % (self.name)

    class Meta:
        permissions = (
            ("alarm_settings", _('can see alarms')),
            ("alarm_test", _('can test alarms')),
        )
        verbose_name = _("alarm")
        verbose_name_plural = _("alarms")
        db_table = "alert"


class AlarmReport(models.Model):
    """This defines the Alarm report

    **Attributes**:

        * ``alarm`` - Alarm name
        * ``calculatedvalue`` - Input the value for the alert
        * ``daterun`` -

    **Name of DB table**: alert_report
    """
    alarm = models.ForeignKey(Alarm, verbose_name=_('alarm'), help_text=_("select Alarm"))
    calculatedvalue = models.DecimalField(verbose_name=_('calculated value'), blank=True, null=True,
                                          max_digits=10, decimal_places=3)
    status = models.PositiveIntegerField(choices=list(ALARM_REPROT_STATUS), verbose_name=_('status'),
                                         default=ALARM_REPROT_STATUS.NO_ALARM_SENT)
    daterun = models.DateTimeField(auto_now_add=True, verbose_name=_('date'))

    def __unicode__(self):
        return '%s' % (self.alarm)

    class Meta:
        permissions = (
            ("alarm_report", _('can see alarm report')),
        )
        verbose_name = _("alarm report")
        verbose_name_plural = _("alarms report")
        db_table = "alert_report"


class Blacklist(models.Model):
    """This defines the Blacklist

    **Attributes**:

        * ``user`` -
        * ``phonenumber_prefix`` -
        * ``country`` -

    **Name of DB table**: alert_blacklist
    """
    user = models.ForeignKey('auth.User', related_name='Blacklist_owner')
    phonenumber_prefix = models.PositiveIntegerField(blank=False, null=False)
    country = models.ForeignKey(Country, null=True, blank=True, verbose_name=_("country"),
                                help_text=_("select country"))

    def __unicode__(self):
        return '[%s] %s' % (self.id, self.phonenumber_prefix)

    class Meta:
        permissions = (
            ("view_blacklist", _('can see blacklist country/prefix')),
        )
        verbose_name = _("blacklist")
        verbose_name_plural = _("blacklist")
        db_table = "alert_blacklist"


class Whitelist(models.Model):
    """This defines the Blacklist

    **Attributes**:

        * ``user`` -
        * ``phonenumber_prefix`` -
        * ``country`` -

    **Name of DB table**: alert_whitelist
    """
    user = models.ForeignKey('auth.User', related_name='whitelist_owner')
    phonenumber_prefix = models.PositiveIntegerField(blank=False, null=False)
    country = models.ForeignKey(Country, null=True, blank=True, verbose_name=_("country"),
                                help_text=_("select country"))

    def __unicode__(self):
        return '[%s] %s' % (self.id, self.phonenumber_prefix)

    class Meta:
        permissions = (
            ("view_whitelist", _('can see whitelist country/prefix')),
        )
        verbose_name = _("whitelist")
        verbose_name_plural = _("whitelist")
        db_table = "alert_whitelist"
