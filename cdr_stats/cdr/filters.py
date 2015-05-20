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

# from django.db import models
# import django_filters
# from django_filters.filters import RangeFilter, DateTimeFilter, DateRangeFilter
# from cdr.models import CDR
from cdr.forms import COMPARE_DICT

#
# this is a work in progress on integrating https://django-filter.readthedocs.org/
#

# Add in views.py
# f = CDRFilter(request.GET, queryset=CDR.objects.filter(destination_number__startswith='+346'))
# pass the following to the template:
# 'filter': f,

# Then in template display with

#     <form action="" method="get">
#         {{ filter.form.as_p }}
#         <input type="submit" />
#     </form>
#     {% for obj in filter %}
#         {{ obj.name }} - ${{ obj.price }}<br />
#     {% endfor %}


# class CDRFilter(django_filters.FilterSet):
#     filter_overrides = {
#         models.CharField: {
#             'filter_class': django_filters.CharFilter,
#             'extra': lambda f: {
#                 'lookup_type': 'icontains',
#             }
#         }
#     }
#     duration = RangeFilter()
#     billsec = RangeFilter()
#     starting_date = DateRangeFilter()

#     class Meta:
#         model = CDR
#         fields = ['switch', 'caller_id_number', 'starting_date', 'duration', 'billsec']


def get_filter_operator_int(base_field, operator):
    """
    convert operators (>, >=, <, <=, =) as django queryset operator
    """
    try:
        operator = int(operator)
    except AttributeError:
        return ""
    result = base_field
    if COMPARE_DICT[operator] == '=':
        result += ''
    elif COMPARE_DICT[operator] == '>':
        result += '__gt'
    elif COMPARE_DICT[operator] == '>=':
        result += '__gte'
    elif COMPARE_DICT[operator] == '<':
        result += '__lt'
    elif COMPARE_DICT[operator] == '<=':
        result += '__lte'
    return result


def get_filter_operator_str(base_field, operator):
    """
    Prepare filters for django queryset
    where fields contain string are checked like
    exact | startswith | contains | endswith
    """
    result = base_field
    if operator == '1':
        result += '__exact'
    elif operator == '2':
        result += '__startswith'
    elif operator == '3':
        result += '__contains'
    elif operator == '4':
        result += '__endswith'
    return result
