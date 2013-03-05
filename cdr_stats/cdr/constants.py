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

from django.utils.translation import ugettext_lazy as _
from common.utils import Choice


class STRING_SEARCH_TYPE_LIST(Choice):
    EQUALS = 1, _('equals').capitalize()
    BEGINS_WITH = 2, _('begins').capitalize()
    CONTAINS = 3, _('contains').capitalize()
    ENDS_WITH = 4, _('ends').capitalize()


class CDR_COLUMN_NAME(Choice):
    call_date = _('call-date')
    clid = _('CLID')
    destination = _('destination')
    duration = _('duration')
    bill = _('bill')
    hangup_cause = _('hangup cause')
    account = _('account')
    buy_rate = _('buy rate')
    buy_cost = _('buy cost')
    sell_rate = _('sell rate')
    sell_cost = _('sell cost')
