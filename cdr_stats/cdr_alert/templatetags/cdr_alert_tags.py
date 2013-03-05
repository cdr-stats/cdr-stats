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
from cdr_alert.constants import PERIOD, ALARM_TYPE, STATUS,\
    ALARM_REPROT_STATUS, ALERT_CONDITION

register = template.Library()


@register.filter(name='alarm_period')
def alarm_period(value):
    """alarm period

    >>> alarm_period(1)
    'START'
    """
    if not value:
        return ''

    period = dict(PERIOD)
    try:
        period = period[value]
    except:
        period = ''

    return str(period)


@register.filter(name='alarm_type')
def alarm_type(value):
    """alarm type

    >>> alarm_type(1)
    'START'
    """
    if not value:
        return ''

    alarm_type = dict(ALARM_TYPE)
    try:
        alarm_type = alarm_type[value]
    except:
        alarm_type = ''

    return str(alarm_type)


@register.filter(name='alarm_status')
def alarm_status(value):
    """alarm status
    """
    if not value:
        return ''
    status = dict(STATUS)
    try:
        status = status[value]
    except:
        status = ''

    return str(status)


@register.filter(name='alarm_condition')
def alarm_condition(value):
    """alarm report status
    """
    if not value:
        return ''
    alarm_condition = dict(ALERT_CONDITION)
    try:
        alarm_condition = alarm_condition[value]
    except:
        alarm_condition = ''

    return str(alarm_condition)


@register.filter(name='alarm_report_status')
def alarm_report_status(value):
    """alarm report status
    """
    if not value:
        return ''
    STATUS = dict(ALARM_REPROT_STATUS)
    try:
        status = STATUS[value]
    except:
        status = ''

    return str(status)

