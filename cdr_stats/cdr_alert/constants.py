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

from django.utils.translation import gettext as _
from common.utils import Choice


class PERIOD(Choice):
    DAY = 1, _('day').capitalize()
    WEEK = 2, _('week').capitalize()
    MONTH = 3, _('month').capitalize()


class STATUS(Choice):
    ACTIVE = 1, _('active').capitalize()
    INACTIVE = 2, _('inactive').capitalize()


class ALARM_TYPE(Choice):
    ALOC = 1, _('ALOC (Average Length of Call)')
    ASR = 2, _('ASR (Answer Seize Ratio)')


class ALERT_CONDITION(Choice):
    IS_LESS_THAN = 1, _('is less than').capitalize()
    IS_GREATER_THAN = 2, _('is greater than').capitalize()
    DECREASE_BY_MORE_THAN = 3, _('decrease by more than').capitalize()
    INCREASE_BY_MORE_THAN = 4, _('increase by more than').capitalize()
    PERCENTAGE_DECREASE_BY_MORE_THAN = 5, _('percentage decrease by more than').capitalize()
    PERCENTAGE_INCREASE_BY_MORE_THAN = 6, _('percentage increase by more than').capitalize()


#This condition only apply if PERIOD is "Day",
#otherwise we will compare to previous week or previous month
class ALERT_CONDITION_ADD_ON(Choice):
    SAME_DAY = 1, _('same day').capitalize()
    SAME_DAY_IN_PRE_WEEK = 2, _('same day in the previous week').capitalize()


class ALARM_REPROT_STATUS(Choice):
    NO_ALARM_SENT = 1, _('no alarm sent').capitalize()
    ALARM_SENT = 2, _('alarm sent').capitalize()


class ALARM_COLUMN_NAME(Choice):
    id = _('ID')
    name = _('name')
    period = _('period')
    type = _('type')
    alert_condition = _('condition')
    alert_value = _('value')
    status = _('status')
    updated_date = _('date')


class ALARM_REPORT_COLUMN_NAME(Choice):
    id = _('ID')
    alarm = _('alarm')
    calculatedvalue = _('calculated value')
    status = _('status')
    date = _('date')
