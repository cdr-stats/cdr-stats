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

from django.utils.translation import ugettext as _
from common.utils import Choice


class NOTICE_TYPE(Choice):
    average_length_of_call = 1, _('average length of call')
    answer_seize_ratio = 2, _('answer seize ratio')
    blacklist_prefix = 3, _('blacklist prefix')
    whitelist_prefix = 4, _('whitelist prefix')


class NOTICE_COLUMN_NAME(Choice):
    message = _('Message')
    notice_type = _('Notice type')
    sender = _('Sender')
    date_field = _('Date')
