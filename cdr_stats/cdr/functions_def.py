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
from country_dialcode.models import Country
from cdr.models import *
from datetime import *
from random import *
import calendar
import string
import urllib
import time


def get_switch_list():
    list = Switch.objects.all()
    return ((l.id, l.name) for l in list)


def get_country_list():
    list = Country.objects.all()
    return ((l.id, l.countryname) for l in list)


def get_hc_list():
    list = HangupCause.objects.all()
    result = []
    for l in list:
        if len(l.enumeration) > 0:
            result.append((l.id, l.enumeration))
        else:
            result.append((l.id, l.cause[:25].upper() + '...'))
    return result


def get_hangupcause_name(id):
    try:
        obj = HangupCause.objects.get(pk=id)
        return obj.enumeration
    except:
        return ''


def get_hangupcause_id(hangupcause_code):
    try:
        obj = HangupCause.objects.get(code=hangupcause_code)
        return obj.id
    except:
        return ''


def get_country_name(id):
    try:
        obj = Country.objects.get(pk=id)
        return obj.countryname
    except:
        return ''


def chk_account_code(request):
    acc_code = ''
    try:
        if not request.user.is_superuser and request.user.get_profile().accountcode is not None:
            acc_code = request.user.get_profile().accountcode
            return acc_code
        else:
            return acc_code
    except :
        return acc_code
