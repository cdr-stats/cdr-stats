# -*- coding: utf-8 -*-

#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2014 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#
from django.conf import settings
from cdr.models import Switch, HangupCause
from country_dialcode.models import Country, Prefix
from cache_utils.decorators import cached
from django.utils.translation import gettext as _
from django_lets_go.common_functions import int_convert_to_minute
import re
import math


def convert_to_minute(value):
    """convert to min"""
    min = int(int(value) / 60)
    sec = int(int(value) % 60)
    return round(float(str(min) + "." + str(sec)), 2)


def get_switch_ip_addr(id):
    """Tag is used to get switch name

    >>> get_switch_ip_addr(0)
    u''
    """
    try:
        return Switch.objects.get(pk=id).name
    except:
        return u''


def get_switch_list():
    """Switch list used in form"""
    return ((l.id, l.name) for l in Switch.objects.all())
    # return ((1, 1)


def get_country_list():
    """Country list used in form"""
    return ((l.id, l.countryname) for l in Country.objects.all())
    return ()


@cached(3600)
def get_hc_list():
    """hangupcause list used in form"""
    return HangupCause.objects.get_all_hangupcause()


@cached(3600)
def get_hangupcause_name(id):
    """Get hangupcause name from its id

    >>> get_hangupcause_name(1)
    'UNSPECIFIED'

    >>> get_hangupcause_name(900)
    ''
    """
    try:
        return HangupCause.objects.get(pk=id).enumeration
    except:
        return ''


@cached(3600)
def get_hangupcause_id(hangupcause_code):
    """Get hangupcause id from its code

    >>> get_hangupcause_id(0)
    1

    >>> get_hangupcause_id(900)
    0
    """
    try:
        return HangupCause.objects.get(code=hangupcause_code).id
    except:
        return 0


def get_hangupcause_id_from_name(hangupcause_name):
    """Get hangupcause id from its code

    >>> get_hangupcause_id_from_name('UNSPECIFIEDD')
    0

    >>> get_hangupcause_id_from_name('NORMAL_CLEARING')
    7
    """
    try:
        return HangupCause.objects.get(enumeration=hangupcause_name).id
    except:
        return 0


def remove_prefix(phonenumber, removeprefix_list):
    # remove the prefix from phone number
    # @ removeprefix_list "+,0,00,000,0000,00000,011,55555,99999"
    #
    # clean : remove spaces
    removeprefix_list = removeprefix_list.strip(' \t\n\r')
    if removeprefix_list and len(removeprefix_list) > 0:
        removeprefix_list = removeprefix_list.split(',')
        removeprefix_list = sorted(removeprefix_list, key=len, reverse=True)
        for rprefix in removeprefix_list:
            rprefix = rprefix.strip(' \t\n\r')
            rprefix = re.sub("\+", "\\\+", rprefix)
            if rprefix and len(rprefix) > 0:
                phonenumber = re.sub('^%s' % rprefix, '', phonenumber)
    return phonenumber


def prefix_list_string(dest_number):
    """
    To return prefix string
    For Example :-
    dest_number = 34650XXXXXX
    prefix_string = (34650, 3465, 346, 34)

    >>> dest_number = 34650123456

    >>> prefix_list_string(dest_number)
    '34650, 3465, 346, 34'

    >>> dest_number = -34650123456

    >>> prefix_list_string(dest_number)
    False
    """
    # Extra number, this is used in case phonenumber is followed by chars
    # ie 34650123456*234
    dest_number = str(dest_number)
    if dest_number[0] == '+':
        dest_number = dest_number[1:]

    m = re.search('(\d*)', dest_number)
    dest_number = m.group(0)
    try:
        int(dest_number)
    except ValueError:
        return False
    prefix_range = range(settings.PREFIX_LIMIT_MIN, settings.PREFIX_LIMIT_MAX + 1)
    prefix_range.reverse()
    destination_prefix_list = ''
    for i in prefix_range:
        if i == settings.PREFIX_LIMIT_MIN:
            destination_prefix_list = destination_prefix_list + dest_number[0:i]
        else:
            destination_prefix_list = destination_prefix_list + dest_number[0:i] + ', '
    return str(destination_prefix_list)


@cached(3600)
def get_country_id_prefix(prefix_list):
    """
    Get country_id and matched prefix from prefix_list
        @ return (country_id, prefix)

    In case of error or not found,
        @ return (None, None)
    """
    country_id = None
    prefix = None
    try:
        # get a list in numeric order (which is also length order)
        prefix_obj = Prefix.objects.filter(prefix__in=eval(prefix_list)).order_by('prefix')
        # find the longest prefix with a non-zero country_id
        for i in xrange(0, len(prefix_obj)):
            if prefix_obj[i].country_id:
                country_id = prefix_obj[i].country_id.id
                prefix = prefix_obj[i].prefix
        return (country_id, prefix)
    except:
        raise
        return (country_id, prefix)


@cached(3600)
def get_country_name(id, type=''):
    """Get country name from its id & return iso2 type name (e.g 'fr')
     or country name

    >>>  get_country_name(198)
    'Spain'

     >>>  get_country_name(198, 'iso2')
    'Spain'
    """
    if id == 999:
        return _('internal Calls')
    try:
        obj = Country.objects.get(pk=id)
        if type == 'iso2':
            return str(obj.iso2).lower()
        else:
            return obj.countryname
    except:
        return _('unknown')


def chk_date_for_hrs(previous_date, graph_date):
    """Check given graph_date is in last 24 hours range

    >>> from datetime import datetime
    >>> graph_date = datetime(2012, 8, 20)

    >>> chk_date_for_hrs(graph_date)
    False
    """
    return True if graph_date > previous_date else False


def calculate_act_acd(total_calls, total_duration):
    """Calculate aggregation on some metrics:

        - ACT: Average Call per Time
        - ACD: Average Call Duration

    TODO:
        - split this function in 2
        - replace ACT by something more meaningful ACH (Average Call per Hour)


    >>> calculate_act_acd(5, 100)
    {'ACD': '00:20', 'ACT': 0.0}
    """
    ACT = math.floor(total_calls / 24)
    if total_calls == 0:
        ACD = 0
    else:
        ACD = int_convert_to_minute(math.floor(total_duration / total_calls))

    return {'ACT': ACT, 'ACD': ACD}
