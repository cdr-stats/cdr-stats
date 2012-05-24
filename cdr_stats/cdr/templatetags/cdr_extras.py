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
from django.template.defaultfilters import *
from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.utils import simplejson
from django.utils.translation import gettext as _
from django import forms
from django.utils.datastructures import SortedDict
from cdr.models import Switch, HangupCause
from datetime import datetime
import operator
import copy
import re

register = template.Library()


@register.filter()
def cal_width(value,max):
    width = (value/float(max))*200
    return width


@register.filter()
def seen_unseen(value):
    if value:
        return "icon-star"
    else:
        return "icon-ok"

    
@register.filter()
def seen_unseen_word(value):
    if value:
        return _("New")
    else:
        return _("Read")


@register.filter()
def notice_count(user):
    """To get unseen notification for admin user & this tag is also used on
       admin template admin/base_site.html"""
    from notification import models as notification
    notice_count = 0
    # get notification count
    try:
        notice_count = notification.Notice.objects.filter(recipient=user, unseen=1).count()
    except:
        pass
    return str(notice_count) + _(" Notification")


@register.filter()
def get_switch_ip(id):
    try:
        obj = Switch.objects.get(pk=id)
        return obj.name
    except:
        return u''


@register.filter()
def get_hangupcause_name(id):
    try:
        obj = HangupCause.objects.get(pk=id)
        return obj.enumeration
    except:
        return ''


@register.filter()
def get_hangupcause_name_with_title(id):
    try:
        obj = HangupCause.objects.get(pk=id)
        val = obj.enumeration
        t = re.sub("([a-z])'([A-Z])", lambda m: m.group(0).lower(), val.title())
        return re.sub("\d([A-Z])", lambda m: m.group(0).lower(), t)
    except:
        return ''


@register.filter()
def mongo_id(value, sub_val):
    if type(value) == type({}):
        if value.has_key('_id'):
            if value['_id'].has_key(sub_val):
                value = int(value['_id'][sub_val])
            else:
                value = value['_id']
    # Return value
    return value


register.filter('cal_width', cal_width)
register.filter('seen_unseen', seen_unseen)
register.filter('seen_unseen_word', seen_unseen_word)
register.filter('notice_count', notice_count)
register.filter('get_switch_ip', get_switch_ip)
register.filter('get_hangupcause_name', get_hangupcause_name)
register.filter('get_hangupcause_name_with_title', get_hangupcause_name_with_title)
register.filter('mongo_id', mongo_id)
