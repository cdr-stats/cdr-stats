# -*- coding: utf-8 -*-
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
# from django.utils.translation import ugettext_lazy as _


def get_status_value(value, STATUS_LIST):
    """common function to get status value

    example: get_status_value(1, EVENT_STATUS)
             get_status_value(3, ALARM_STATUS)
    """
    if not value:
        return ''
    STATUS = dict(STATUS_LIST)
    try:
        return STATUS[value].encode('utf-8')
    except:
        return ''
