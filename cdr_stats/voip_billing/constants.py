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

from django.utils.translation import ugettext as _
from common.utils import Choice


class LCR_TYPE(Choice):
    LCR = 0, _('LCR')
    LCD = 1, _('LCD')


class CONFIRMATION_TYPE(Choice):
    YES = 'YES', _('Yes')
    NO = 'NO', _('No')


class RATE_COLUMN_NAME(Choice):
    prefix = _('prefix')
    destination = _('destination')
    rate = _('rate')
