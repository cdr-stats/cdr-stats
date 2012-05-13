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
from cdr_alert.models import Blacklist, Whitelist
from cdr_alert.tasks import blacklist_whitelist_notification
from random import *
import calendar
import string
import urllib
import time


def chk_prefix_in_whitelist(prefix_list):
    """Check destination no with allowed prefix"""
    if not prefix_list:
        return False
    white_prefix_list = Whitelist.objects.all()
    flag = False
    if white_prefix_list:
        for j in eval(prefix_list):
            for i in white_prefix_list:
                # Allowed Prefix
                if i.phonenumber_prefix == j:
                    flag = True
                    break

            # if flag is true
            # allowed
            if flag:
                # TODO: Send alert
                blacklist_whitelist_notification.delay(4) # notice_type = 4 whitelist
                return True

    # no whitelist define
    return False


def chk_prefix_in_blacklist(prefix_list):
    """Check destination no with ban prefix"""
    if not prefix_list:
        return True
    banned_prefix_list = Blacklist.objects.all()
    flag = False
    if banned_prefix_list:
        for j in eval(prefix_list):
            for i in banned_prefix_list:
                # Banned Prefix
                if i.phonenumber_prefix == j:
                    flag = True
                    break

            # if flag is true
            # not allowed
            if flag:
                # TODO: Send alert
                blacklist_whitelist_notification.delay(3) # notice_type = 3 blacklist
                return False

    # no blacklist is defined
    return True