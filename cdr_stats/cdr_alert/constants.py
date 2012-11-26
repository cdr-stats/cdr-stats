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

from django.utils.translation import gettext as _
from common.utils import Choice


class PERIOD(Choice):
    DAY = 1, _('Day')
    WEEK = 2, _('Week')
    MONTH = 3, _('Month')


class STATUS(Choice):
    ACTIVE = 1, _('Active')
    INACTIVE = 2, _('Inactive')


class ALARM_TYPE(Choice):
    ALOC = 1, _('ALOC (Average Length of Call)')
    ASR = 2, _('ASR (Answer Seize Ratio)')


class ALERT_CONDITION(Choice):
    IS_LESS_THAN = 1, _('Is less than')
    IS_GREATER_THAN = 2, _('Is greater than')
    DECREASE_BY_MORE_THAN = 3, _('Decrease by more than')
    INCREASE_BY_MORE_THAN = 4, _('Increase by more than')
    PERCENTAGE_DECREASE_BY_MORE_THAN = 5, _('Percentage decrease by more than')
    PERCENTAGE_INCREASE_BY_MORE_THAN = 6, _('Percentage increase by more than')


#This condition only apply if PERIOD is "Day",
#otherwise we will compare to previous week or previous month
class ALERT_CONDITION_ADD_ON(Choice):
    SAME_DAY = 1, _('Same day')
    SAME_DAY_IN_PRE_WEEK = 2, _('Same day in the previous week')


class ALARM_REPROT_STATUS(Choice):
    NO_ALARM_SENT = 1, _('No alarm sent')
    ALARM_SENT = 2, _('Alarm Sent')


class ALARM_COLUMN_NAME(Choice):
    id = _('ID')
    name = _('Name')
    period = _('Period')
    type = _('Type')
    email_to_send_alarm = _('Email send to')
    updated_date = _('Date')