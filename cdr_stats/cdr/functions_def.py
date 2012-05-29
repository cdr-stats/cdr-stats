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
from django.conf import settings
from django.utils.translation import gettext as _
from cdr.models import Switch, HangupCause
from country_dialcode.models import Country, Prefix

from datetime import *
import re


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
        return 0


def remove_prefix(phonenumber, removeprefix_list):
    # remove the prefix from phone number
    # @ removeprefix_list "+,0,00,000,0000,00000,011,55555,99999"
    #
    #clean : remove spaces
    removeprefix_list = removeprefix_list.strip(' \t\n\r')
    if removeprefix_list and len(removeprefix_list) > 0:
        removeprefix_list = removeprefix_list.split(",")
        removeprefix_list = sorted(removeprefix_list, key=len, reverse=True)
        for rprefix in removeprefix_list:
            rprefix = rprefix.strip(' \t\n\r')
            rprefix = re.sub("\+", "\\\+", rprefix)
            if rprefix and len(rprefix) > 0:
                phonenumber = re.sub("^%s" % rprefix, "", phonenumber)
    return phonenumber


def prefix_list_string(phone_number):
    """
    To return prefix string
    For Example :-
    phone_no = 34650XXXXXX
    prefix_string = (34650, 3465, 346, 34)
    """
    try:
        int(phone_number)
    except ValueError:
        return False
    phone_number = str(phone_number)
    prefix_range = range(settings.PHONENUMBER_PREFIX_LIMIT_MIN,
                         settings.PHONENUMBER_PREFIX_LIMIT_MAX + 1)
    prefix_range.reverse()
    destination_prefix_list = ''
    for i in prefix_range:
        if i == settings.PHONENUMBER_PREFIX_LIMIT_MIN:
            destination_prefix_list = destination_prefix_list +\
                                      phone_number[0:i]
        else:
            destination_prefix_list = destination_prefix_list +\
                                      phone_number[0:i] + ', '
    return str(destination_prefix_list)


def get_country_id(prefix_list):
    try:
        prefix_obj = Prefix.objects.filter(prefix__in=eval(prefix_list))
        country_id = prefix_obj[0].country_id.id
    except:
        country_id = 0
    return country_id


def get_country_name(id, type=''):
    try:
        obj = Country.objects.get(pk=id)
        if type == 'iso2':
            return str(obj.iso2).lower()
        else:
            return obj.countryname
    except:
        return ''


def chk_account_code(request):
    acc_code = ''
    try:
        if not request.user.is_superuser \
            and request.user.get_profile().accountcode is not None:
            acc_code = request.user.get_profile().accountcode
            return "%s" % str(acc_code)
        else:
            return "%s" % str(acc_code)
    except:
        return acc_code
