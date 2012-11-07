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
from django import template
from django.utils.translation import gettext as _
from cdr.models import Switch
from cdr.functions_def import get_hangupcause_name
from cdr.views import notice_count
import re

register = template.Library()


@register.filter(name='seen_unseen')
def seen_unseen(value):
    """Tag is for icon which is
    used on user notification list

    >>> seen_unseen('1')
    'icon-star'

    >>> seen_unseen('')
    'icon-ok'
    """
    if value:
        return "icon-star"
    else:
        return "icon-ok"


@register.filter(name='seen_unseen_word')
def seen_unseen_word(value):
    """Tag is for notification status which is
    used on user notification list

    >>> seen_unseen_word('1')
    'New'

    >>> seen_unseen_word('')
    'Read'
    """
    if value:
        return _("New")
    else:
        return _("Read")


@register.filter(name='get_switch_ip')
def get_switch_ip(id):
    """Tag is used to get switch name

    >>> get_switch_ip(0)
    u''
    """
    try:
        obj = Switch.objects.get(pk=id)
        return obj.name
    except:
        return u''


@register.filter(name='hangupcause_name')
def hangupcause_name(id):
    """Tag is used to get hangupcause name"""
    return get_hangupcause_name(id)


@register.filter(name='hangupcause_name_with_title')
def hangupcause_name_with_title(id):
    """Tag is used to get hangupcause name with lowercase

    >>> hangupcause_name_with_title(10000)
    ''
    """
    try:
        val = get_hangupcause_name(id)
        t = re.sub("([a-z])'([A-Z])", lambda m: m.group(0).lower(), val.title())
        return re.sub("\d([A-Z])", lambda m: m.group(0).lower(), t)
    except:
        return ''


@register.filter(name='mongo_id')
def mongo_id(value, sub_val):
    """Tag is used to get mongo mapreduce _id.value"""
    if type(value) == type({}):
        if '_id' in value:
            if sub_val in value['_id']:
                value = int(value['_id'][sub_val])
            else:
                value = value['_id']
    # Return value
    return value


@register.simple_tag(name='get_notice_count')
def get_notice_count(request):
    """tag to display notice count"""
    return notice_count(request)
