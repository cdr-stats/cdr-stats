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
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from country_dialcode.models import Country, Prefix
import re


PERIOD  = (
    (1, _('Day')),
    (2, _('Week')),
    (3, _('Month')),
)

STATUS = (
    (1, _('Active')),
    (2, _('Inactive')),
)

ALARM_TYPE = (
    (1, _('ALOC (Average Length of Call)')),
    (2, _('ASR (Answer Seize Ratio)')),
)

ALERT_CONDITION  = (
    (1, _('Is less than')),
    (2, _('Is greater than')),
    (3, _('Decrease by more than')),
    (4, _('Increase by more than')),
    (5, _('% decrease by more than')),
    (6, _('% Increase by more than')),
)

#this condition only apply if PERIOD is "Day", otherwise we will compare to previous week or previous month
ALERT_CONDITION_ADD_ON  = (
    (1, _('Same day')),
    (2, _('Same day in the previous week')),
)

ALARM_REPROT_STATUS  = (
    (1, _('No alarm sent')),
    (2, _('Alarm Sent')),
)


class AlertRemovePrefix(models.Model):
    """This defines the Alert Remove Prefix
    Here you can define the list of prefixes that need to be removed from the dialed digits,
    imagine all your phone numbers are in the format 5555004432111321
    You will need to remove the prefix 5555 in order to analyze the phone numbers

    **Attributes**:

        * ``label`` - Label for the custom prefix
        * ``prefix`` - Prefix value

    **Name of DB table**: alarm
    """
    label  = models.CharField(max_length=100, verbose_name=_('Label'))
    prefix  = models.CharField(max_length=100, unique=True,
                                    verbose_name=_('Prefix'))
    created_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name=_('Date'))
    updated_date = models.DateTimeField(auto_now=True)


    def __unicode__(self):
        return '%s' %(self.label)

    class Meta:
        verbose_name = _("Alert Remove Prefix")
        verbose_name_plural = _("Alert Remove Prefixes")
        db_table = "alert_remove_prefix"

class Alarm(models.Model):
    """This defines the Alarm

    **Attributes**:

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
    name  = models.CharField(max_length=100, verbose_name=_('Name'))
    period = models.PositiveIntegerField(choices=PERIOD, default=1,
                                         verbose_name=_('Period'),
                                         help_text=_('Interval to apply alarm'))
    type = models.PositiveIntegerField(choices=ALARM_TYPE, default=1,
                                       verbose_name=_('Type'),
                                       help_text=_('ALOC (average length of call) ; ASR (answer seize ratio) ; CIC (Consecutive Incomplete Calls) '))
    alert_condition = models.PositiveIntegerField(choices=ALERT_CONDITION, default=1,
                                                  verbose_name=_('Condition'))
    alert_value = models.DecimalField(verbose_name=_('Value'), max_digits=5,
                                  decimal_places=2, blank=True, null=True,
                                  help_text=_('Input the value for the alert'))
    alert_condition_add_on = models.PositiveIntegerField(choices=ALERT_CONDITION_ADD_ON,
                                                         default=1)

    status = models.PositiveIntegerField(choices=STATUS, default=1,
                                         verbose_name=_('Status'))

    email_to_send_alarm = models.EmailField(max_length=100,
                                            verbose_name=_('Email to send alarm'))
    created_date = models.DateTimeField(auto_now_add=True,
                                        verbose_name=_('Date'))
    updated_date = models.DateTimeField(auto_now=True)


    def __unicode__(self):
        return '%s' %(self.name)

    class Meta:
        verbose_name = _("Alarm")
        verbose_name_plural = _("Alarms")
        db_table = "alert"



class AlarmReport(models.Model):
    """This defines the Alarm report

    **Attributes**:

        * ``alarm`` - Alarm name
        * ``calculatedvalue`` - Input the value for the alert
        * ``daterun`` -

    **Name of DB table**: alert_report
    """
    alarm  = models.ForeignKey(Alarm, verbose_name=_('Alarm'),
                               help_text=_("Select Alarm"))
    calculatedvalue = models.DecimalField(verbose_name=_('Calculated value'),
                                          max_digits=10, decimal_places=3,
                                          blank=True, null=True)
    status = models.PositiveIntegerField(choices=ALARM_REPROT_STATUS, default=1,
                                                  verbose_name=_('Status'))

    daterun = models.DateTimeField(auto_now=True, verbose_name=_('Date'))

    def __unicode__(self):
        return '%s' %(self.alarm)

    class Meta:
        verbose_name = _("Alarm Report")
        verbose_name_plural = _("Alarms Report")
        db_table = "alert_report"


class Blacklist(models.Model):
    """This defines the Blacklist

    **Attributes**:

        * ``phonenumber_prefix`` -
        * ``country`` -

    **Name of DB table**: alert_blacklist
    """
    phonenumber_prefix = models.PositiveIntegerField(blank=False, null=False)
    country = models.ForeignKey(Country, null=True, blank=True,
                                verbose_name=_("Country"),
                                help_text=_("Select Country"))

    def __unicode__(self):
        return '[%s] %s' %(self.id, self.phonenumber_prefix)

    class Meta:
        verbose_name = _("Blacklist")
        verbose_name_plural = _("Blacklist")
        db_table = "alert_blacklist"


class Whitelist(models.Model):
    """This defines the Blacklist

    **Attributes**:

        * ``phonenumber_prefix`` -
        * ``country`` -

    **Name of DB table**: alert_whitelist
    """
    phonenumber_prefix = models.PositiveIntegerField(blank=False, null=False)
    country = models.ForeignKey(Country, null=True, blank=True,
                                verbose_name=_("Country"),
                                help_text=_("Select Country"))
    def __unicode__(self):
        return '[%s] %s' %(self.id, self.phonenumber_prefix)

    class Meta:
        verbose_name = _("Whitelist")
        verbose_name_plural = _("Whitelist")
        db_table = "alert_whitelist"
