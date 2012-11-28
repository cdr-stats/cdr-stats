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

from dajaxice.decorators import dajaxice_register
from dajax.core import Dajax

from cdr_alert.models import Whitelist, Blacklist
from cdr.functions_def import remove_prefix,\
    prefix_list_string, get_country_id
from country_dialcode.models import Country, Prefix

def get_table_string(request, default_name='blacklist'):
    col = 3
    row = 1

    if default_name == 'blacklist':
        prefix_list = Blacklist.objects.filter(user=request.user)
        prefix_list_count = prefix_list.count()

    if default_name == 'whitelist':
        prefix_list = Whitelist.objects.filter(user=request.user)
        prefix_list_count = prefix_list.count()

    result_table = '<table class="table table-striped table-bordered table-condensed"><tr>'
    total_row = 1
    for obj in prefix_list:
        obj_string = str(obj.phonenumber_prefix) + ' | ' + str(obj.country.countryname)
        if row % col == 0:
            result_table += '<td>' + str(obj_string) + '</td></tr><tr>'
            row = 1
            total_row += 1
        else:
            result_table += '<td>' + str(obj_string)  + '</td>'
            row += 1


    remaining_rows = prefix_list_count % (total_row-1)
    if remaining_rows != 0:
        for i in range(0, remaining_rows):
            result_table += '<td>&nbsp;</td>'

    result_table += '</tr></table>'

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
            result = '<div class="alert alert-success">Alert : (%s) has been successfully added in blacklist !!</div>' % (country.countryname)
        else:
            result = '<div class="alert alert-error">Alert : (%s) already added in blacklist !!</div>' % (country.countryname)

        result_table = get_table_string(request, default_name='blacklist')

        #print result_table
        dajax.assign('#id_alert_success', 'innerHTML', str(result))
        dajax.assign('#id_blacklist_table', 'innerHTML', str(result_table))

    except:
        pass
        #dajax.alert("%s is not exist !!" % (id))
        #for error in form.errors:
        #    dajax.add_css_class('#id_%s' % error, 'error')
    return dajax.json()


@login_required
@dajaxice_register
def add_blacklist_prefix(request, prefix):
    dajax = Dajax()

    try:
        prefix_list =\
            list(Prefix.objects.values_list('prefix', flat=True).filter(prefix=int(prefix)))

        country_id = get_country_id(str(prefix_list))

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
             result = '<div class="alert alert-success">Alert : (%s) has been successfully added in blacklist !!</div>' \
                 % (str(prefix))
        else:
            result = '<div class="alert alert-error">Alert : (%s) already added in blacklist !!</div>'\
                     % (str(prefix))

        result_table = get_table_string(request, default_name='blacklist')
        dajax.assign('#id_alert_success', 'innerHTML', str(result))
        dajax.assign('#id_blacklist_table', 'innerHTML', str(result_table))
    except:
        pass
        #dajax.alert("%s is not exist !!" % (id))
        #for error in form.errors:
        #    dajax.add_css_class('#id_%s' % error, 'error')
    return dajax.json()
