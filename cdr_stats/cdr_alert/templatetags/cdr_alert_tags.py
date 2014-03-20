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
from django import template
from django.utils.safestring import mark_safe
from cdr_alert.constants import PERIOD, ALARM_TYPE, STATUS, ALARM_REPROT_STATUS, ALERT_CONDITION,\
    ALERT_CONDITION_ADD_ON
from mod_utils.function_def import get_status_value
from country_dialcode.models import Prefix
register = template.Library()


@register.filter(name='alarm_period')
def alarm_period(value):
    """alarm period

    >>> alarm_period(1)
    'START'
    """
    return get_status_value(value, PERIOD)


@register.filter(name='alarm_type')
def alarm_type(value):
    """alarm type

    >>> alarm_type(1)
    'START'
    """
    return get_status_value(value, ALARM_TYPE)


@register.filter(name='alarm_status')
def alarm_status(value):
    """alarm status"""
    return get_status_value(value, STATUS)


@register.filter(name='alarm_condition')
def alarm_condition(value):
    """alarm report status"""
    return get_status_value(value, ALERT_CONDITION)


@register.filter(name='alarm_condition_add_on')
def alarm_condition_add_on(value):
    """alarm condition add_on"""
    return get_status_value(value, ALERT_CONDITION_ADD_ON)


@register.filter(name='alarm_report_status')
def alarm_report_status(value):
    """alarm report status"""
    return get_status_value(value, ALARM_REPROT_STATUS)


@register.simple_tag(name='get_prefixes')
def get_prefixes():
    """Usage: {% get_prefixes %}"""
    prefix_list = map(str, Prefix.objects.values_list("prefix", flat=True).all().order_by('prefix'))
    prefix_list = (','.join('"' + item + '"' for item in prefix_list))
    prefix_list = "[" + str(prefix_list) + "]"
    return mark_safe(prefix_list)
