# -*- coding: utf-8 -*-
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

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _

from dajaxice.decorators import dajaxice_register
from dajax.core import Dajax

from cdr_alert.models import Whitelist, Blacklist
from cdr.functions_def import remove_prefix,\
    prefix_list_string, get_country_id
from country_dialcode.models import Country, Prefix


blacklist_success = '<div class="alert alert-success">Alert : (%s) has been successfully added in blacklist !!</div>'
blacklist_info = '<div class="alert alert-info">Alert : (%s) is already added in blacklist !!</div>'
blacklist_error = '<div class="alert alert-error">Alert : (%s) has not been added in blacklist !!</div>'


whitelist_success = '<div class="alert alert-success">Alert : (%s) has been successfully added in whitelist !!</div>'
whitelist_info = '<div class="alert alert-info">Alert : (%s) already added in whitelist !!</div>'
whitelist_error = '<div class="alert alert-error">Alert : (%s) has not been added in whitelist !!</div>'


def get_table_string(request, default_name='blacklist'):
    col = 3 # group by columns

    if default_name == 'blacklist':
        prefix_list = Blacklist.objects.filter(user=request.user).order_by('id')
        prefix_list_count = prefix_list.count()

    if default_name == 'whitelist':
        prefix_list = Whitelist.objects.filter(user=request.user).order_by('id')
        prefix_list_count = prefix_list.count()

    result_table = '<table class="table table-striped table-bordered table-condensed">'

    # same logic of groupby_columns template tag
    rows = (prefix_list_count // col) + 1

    table = [prefix_list[i::rows] for i in range(rows)]

    n = len(table[0])
    new_prefix_list = [row + [None for x in range(n - len(row))] for row in table]
    for obj_list in new_prefix_list:
        result_table += '<tr>'
        for obj in obj_list:
            if obj:
                obj_string = str(obj.phonenumber_prefix) + ' | ' + str(obj.country.countryname)
                result_table += '<td>' + str(obj_string) + '</td>'
            else:
                result_table += '<td>&nbsp;</td>'

        result_table += '</tr>'

    result_table += '</table>'

    return result_table





@login_required
@dajaxice_register
def add_blacklist_country(request, country_id):
    dajax = Dajax()
    try:
        country = Country.objects.get(id=int(country_id))

        country_id = country.id
        prefix_list =\
            Prefix.objects.values_list('prefix', flat=True).filter(country_id=country_id)

        add_flag = False

        for prefix in prefix_list:
            rec_count = Blacklist.objects.filter(user=request.user,
                                                 phonenumber_prefix=int(prefix),
                                                 country_id=country_id).count()

            # No duplicate record, so insert
            if rec_count == 0:
                blacklist = Blacklist.objects.create(
                    user=request.user,
                    phonenumber_prefix=int(prefix),
                    country_id=country_id,
                )
                add_flag = True
        if add_flag:
            result = blacklist_success % (country.countryname)
        else:
            result = blacklist_info % (country.countryname)

        result_table = get_table_string(request, 'blacklist')
        dajax.assign('#id_blacklist_table', 'innerHTML', str(result_table))
    except:
        result = blacklist_error % (country.countryname)

    dajax.assign('#id_alert_message', 'innerHTML', str(result))
    return dajax.json()


@login_required
@dajaxice_register
def add_blacklist_prefix(request, prefix):
    dajax = Dajax()

    try:
        prfix_obj = Prefix.objects.get(prefix=int(prefix))
        country_id = prfix_obj.country_id

        rec_count = Blacklist.objects.filter(user=request.user,
            phonenumber_prefix=int(prefix),
            country_id=country_id).count()

        add_flag = False
        # No duplicate record, so insert
        if rec_count == 0:
            blacklist = Blacklist.objects.create(
                user=request.user,
                phonenumber_prefix=int(prefix),
                country_id=country_id,
            )
            add_flag = True

        if add_flag:
            result = blacklist_success % (str(prefix))
        else:
            result = blacklist_info % (str(prefix))

        result_table = get_table_string(request, 'blacklist')

        dajax.assign('#id_blacklist_table', 'innerHTML', str(result_table))
    except:
        result = blacklist_error % (prefix)
    dajax.assign('#id_alert_message', 'innerHTML', str(result))
    return dajax.json()


## whitelist

@login_required
@dajaxice_register
def add_whitelist_country(request, country_id):
    dajax = Dajax()
    try:
        country = Country.objects.get(id=int(country_id))

        country_id = country.id
        prefix_list =\
            Prefix.objects.values_list('prefix', flat=True).filter(country_id=country_id)

        add_flag = False

        for prefix in prefix_list:
            rec_count = Whitelist.objects.filter(user=request.user,
                                                 phonenumber_prefix=int(prefix),
                                                 country_id=country_id).count()

            # No duplicate record, so insert
            if rec_count == 0:
                whitelist = Whitelist.objects.create(
                    user=request.user,
                    phonenumber_prefix=int(prefix),
                    country_id=country_id,
                )
                add_flag = True
        if add_flag:
            result = whitelist_success % (country.countryname)
        else:
            result = whitelist_info % (country.countryname)

        result_table = get_table_string(request, 'whitelist')
        dajax.assign('#id_whitelist_table', 'innerHTML', str(result_table))
    except:
        result = whitelist_error % (str(prefix))
    dajax.assign('#id_alert_message', 'innerHTML', str(result))
    return dajax.json()


@login_required
@dajaxice_register
def add_whitelist_prefix(request, prefix):
    dajax = Dajax()

    try:
        prfix_obj = Prefix.objects.get(prefix=int(prefix))
        country_id = prfix_obj.country_id

        rec_count = Whitelist.objects.filter(user=request.user,
                                             phonenumber_prefix=int(prefix),
                                             country_id=country_id).count()

        add_flag = False
        # No duplicate record, so insert
        if rec_count == 0:
            whitelist = Whitelist.objects.create(
                user=request.user,
                phonenumber_prefix=int(prefix),
                country_id=country_id,
            )
            add_flag = True

        if add_flag:
            result = whitelist_success % (str(prefix))
        else:
            result = whitelist_info % (str(prefix))

        result_table = get_table_string(request, 'whitelist')
        dajax.assign('#id_whitelist_table', 'innerHTML', str(result_table))
    except:
        result = whitelist_error % (str(prefix))
    dajax.assign('#id_alert_message', 'innerHTML', str(result))
    return dajax.json()