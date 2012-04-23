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
from cdr.models import Switch
from datetime import datetime
import operator
import copy

register = template.Library()

@register.filter()
def time_in_min(value,arg):
    if int(value)!=0:
        if arg == 'min':
            min = int(value / 60)
            sec = int(value % 60)
            return "%02d" % min + ":" + "%02d" % sec + "min"
        else:
            min = int(value / 60)
            min = (min * 60)
            sec = int(value % 60)
            total_sec = min + sec
            return str(total_sec + " sec")
    else:
        return str("00:00 min")

@register.filter()
def conv_min(value):
    if int(value)!=0:
        min = int(value / 60)
        sec = int(value % 60)
        return "%02d" % min + ":" + "%02d" % sec
    else:
        return "00:00"

@register.filter()
def month_int(value):
    val=int(value[0:2])
    return val

@register.filter()
def month_name(value,arg):
    month_dict = {1:"Jan",2:"Feb",3:"Mar",4:"Apr", 5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    no=int(value)
    m_name = month_dict[no]
    return str(m_name) + " " + str(arg)

@register.filter()
def cal_width(value,max):
    width = (value/float(max))*200
    return width

@register.filter
def to_json(value):
    return mark_safe(simplejson.dumps(value))


@register.inclusion_tag('cdr/sort_link_frag.html', takes_context=True)
def sort_link(context, link_text, sort_field, visible_name=None):
    """Usage: {% sort_link "link text" "field_name" %}
    Usage: {% sort_link "link text" "field_name" "Visible name" %}
    """
    is_sorted = False
    sort_order = None
    orig_sort_field = sort_field
    if context.get('current_sort_field') == sort_field:
        sort_field = '-%s'%sort_field
        visible_name = '-%s'%(visible_name or orig_sort_field)
        is_sorted = True
        sort_order = 'down'
    elif context.get('current_sort_field') == '-'+sort_field:
        visible_name = '%s'%(visible_name or orig_sort_field)
        is_sorted = True
        sort_order = 'up'

    if visible_name:
        if 'request' in context:
            request = context['request']
            request.session[visible_name] = sort_field

    if 'getsortvars' in context:
        extra_vars = context['getsortvars']
    else:
        if 'request' in context:
            request = context['request']
            getvars = request.GET.copy()
            if 'sort_by' in getvars:
                del getvars['sort_by']
            if len(getvars.keys()) > 0:
                context['getsortvars'] = "&%s" % getvars.urlencode()
            else:
                context['getsortvars'] = ''
            extra_vars = context['getsortvars']

        else:
            extra_vars = ''


    return {'link_text':link_text, 'sort_field':sort_field, 'extra_vars':extra_vars,
            'sort_order':sort_order, 'is_sorted':is_sorted, 'visible_name':visible_name
            }


@register.tag
def auto_sort(parser, token):
    "usage: {% auto_sort queryset %}"
    try:
        tag_name, queryset = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a single argument" % token.contents.split()[0]
    return SortedQuerysetNode(queryset)

class SortedQuerysetNode(template.Node):
    def __init__(self, queryset):
        self.queryset_var = queryset
        self.queryset = template.Variable(queryset)

    def render(self, context):
        queryset = self.queryset.resolve(context)
        if 'request' in context:
            request = context['request']
            sort_by = request.GET.get('sort_by')
            has_visible_name = False
            if sort_by:
                if sort_by in [el.name for el in queryset.model._meta.fields]:
                    queryset = queryset.order_by(sort_by)
                else:
                    has_visible_name = True
                    if sort_by in request.session:
                        sort_by = request.session[sort_by]
                        try:
                            queryset = queryset.order_by(sort_by)
                        except:
                            raise
        context[self.queryset_var] = queryset
        if 'request' in context:
            getvars = request.GET.copy()
        else:
            getvars = {}
        if 'sort_by' in getvars:
            if has_visible_name:
                context['current_sort_field']= request.session.get(getvars['sort_by']) or getvars['sort_by']
            else:
                context['current_sort_field']= getvars['sort_by']
            del getvars['sort_by']
        if len(getvars.keys()) > 0:
            context['getsortvars'] = "&%s" % getvars.urlencode()
        else:
            context['getsortvars'] = ''
        return ''

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


def get_fieldset(parser, token):
    try:
        name, fields, as_, variable_name, from_, form = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError('bad arguments for %r'  % token.split_contents()[0])

    return FieldSetNode(fields.split(','), variable_name, form)

get_fieldset = register.tag(get_fieldset)


class FieldSetNode(template.Node):
    def __init__(self, fields, variable_name, form_variable):
        self.fields = fields
        self.variable_name = variable_name
        self.form_variable = form_variable

    def render(self, context):

        form = template.Variable(self.form_variable).resolve(context)
        new_form = copy.copy(form)
        new_form.fields = SortedDict([(key, value) for key, value in form.fields.items() if key in self.fields])

        context[self.variable_name] = new_form

        return u''


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

def _regroup_table(seq, rows=None, columns=None):
    if not (rows or columns):
        raise ArgumentError("Missing one of rows or columns")

    if columns:
        rows = (len(seq) // columns) + 1
    table = [seq[i::rows] for i in range(rows)]

    # Pad out short rows
    n = len(table[0])
    return [row + [None for x in range(n - len(row))] for row in table]


@register.filter
def groupby_rows(seq, n):
    """Returns a list of n lists. Each sub-list is the same length.

    Short lists are padded with None. This is useful for creating HTML tables
    from a sequence.

    >>> groupby_rows(range(1, 11), 3)
    [[1, 4, 7, 10], [2, 5, 8, None], [3, 6, 9, None]]
    """
    return _regroup_table(seq, rows=int(n))


@register.filter
def groupby_columns(seq, n):
    """Returns a list of lists where each sub-list has n items.

    Short lists are padded with None. This is useful for creating HTML tables
    from a sequence.

    >>> groupby_columns(range(1, 11), 3)
    [[1, 5, 9], [2, 6, 10], [3, 7, None], [4, 8, None]]
    """
    return _regroup_table(seq, columns=int(n))


register.filter('conv_min', conv_min)
register.filter('time_in_min', time_in_min)
register.filter('month_int', month_int)
register.filter('month_name', month_name)
register.filter('cal_width', cal_width)
register.filter('to_json', to_json)
register.filter('seen_unseen', seen_unseen)
register.filter('seen_unseen_word', seen_unseen_word)
register.filter('notice_count', notice_count)
register.filter('get_switch_ip', get_switch_ip)
register.filter('groupby_rows', groupby_rows)
register.filter('groupby_columns', groupby_columns)