#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2015 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#
from dilla import spam
import string
import random
import logging


log = logging.getLogger('dilla')


@spam.strict_handler('provider.Provider.metric')
def spam_provider_metric_field(field):
    return random.randint(1, 10)


@spam.global_handler('TextField')
def spam_provider_char_field2(field):
    return random.choice(string.ascii_letters)
