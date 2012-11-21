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

from django.utils.translation import ugettext_lazy as _
from common.utils import Choice


class STRING_SEARCH_TYPE_LIST(Choice):
    EQUALS = 1, _('Equals')
    BEGINS_WITH = 2, _('Begins')
    CONTAINS = 3, _('Contains')
    ENDS_WITH = 4, _('Ends')


class CDR_COLUMN_NAME(Choice):
    call_date = _('Call-date')
    clid = _('CLID')
    destination = _('Destination')
    duration = _('Duration')
    bill = _('Bill')
    hangup_cause = _('Hangup cause')
    account = _('Account')
