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

import six
import pprint
from datetime import datetime


def pp(data, ro=False):

    """Format for pretty print."""
    if not ro:
        pprint.pprint(data, indent=4, width=10)
    return pprint.pformat(data, indent=4, width=10)


def trunc_date_start(date, trunc_hour_min=False):
    """
    Convert a string date to a start date

    trunc_min allows to trunc the date to the minute
    """
    if isinstance(date, six.string_types):
        date = datetime.strptime(date, '%Y-%m-%d %H:%M')

    (hour, minute, second, millisec) = (0, 0, 0, 0)

    return datetime(date.year, date.month, date.day, hour, minute, second, millisec)


def trunc_date_end(date, trunc_hour_min=False):
    """
    Convert a string date to a end date

    trunc_min allows to trunc the date to the minute
    """
    if isinstance(date, six.string_types):
        date = datetime.strptime(date, '%Y-%m-%d %H:%M')

    (hour, minute, second, millisec) = (23, 59, 59, 999999)

    return datetime(date.year, date.month, date.day, hour, minute, second, millisec)
